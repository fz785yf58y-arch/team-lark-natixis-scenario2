#!/usr/bin/env python3
"""Offline reproduction of frozen marks, note engines, metrics and sensitivity.

This verifies the published research calculation. It does not replace the
missing point-in-time security master or regenerate licensed raw price inputs.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lark.metrics import stats, weekly_marks
from lark import commodity_note, crypto_note, equity_note_roll, curve

CAP={'ficc':60e6,'equities':25e6,'commodities':5e6,'crypto':5e6,'fx':5e6,'total':100e6}

def read(rel):
    return pd.read_csv(ROOT/rel,parse_dates=['date']).set_index('date').sort_index()

def checksum(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def note_rebuild(kind,module):
    d=read(f'data/frozen/{kind}_note_inputs.csv')
    days=[x.date() for x in d.index]
    index=dict(zip(days,d.underlying_index));sigma=dict(zip(days,d.sigma))
    curves={day:{float(k):v for k,v in json.loads(s).items()} for day,s in zip(days,d.treasury_curve)}
    # These causal volatilities were computed with warmup data in the original
    # run. Freezing them avoids inventing missing pre-inception history.
    module.trailing_sigma=lambda _, dates, i, *args, **kwargs:sigma[dates[i]]
    module.last_known_curve=lambda _, day:curves[day]
    costs=dict(zip(days,d.basket_rebalance_cost_fraction))
    spec=module.note_spec(f'{kind}_retained','commodity' if kind=='commodity' else 'crypto','par_budget',None,0. if kind=='commodity' else 1.,'retained')
    rows,issues,cashflows=module.simulate_note(spec,days,index,curves,market_turnover_costs=costs)
    out=pd.DataFrame(rows);out['date']=pd.to_datetime(out.date)
    return out.set_index('date').nav_usd,issues

def equity_rebuild():
    d=read('data/frozen/equity_note_inputs.csv')
    raw=pd.read_csv(ROOT/'data/official/fed_svensson_coefficients.csv')
    curves={pd.Timestamp(row.Date).date():tuple(float(getattr(row,k)) for k in ['BETA0','BETA1','BETA2','BETA3','TAU1','TAU2']) for row in raw.itertuples()}
    curve.read_curve=lambda:curves
    nav,issues=equity_note_roll.price_note(d.underlying_index,d.index,d.sigma)
    return nav*25e6,issues

def forward_case():
    p=json.loads((ROOT/'data/parameters/ficc_forward_20y.json').read_text())
    b=p['budget_reconciliation']; y=p['credit_yield_proxy']['weighted_six_bond_eay_pct']/100
    cash_yield=0.0368226235; credit=b['credit_growth_pool_after_strip_cost_adjustment_usd']; strip=b['60m_face_strip_market_cost_usd']
    cash=b['vusxx_cash_usd']; years=p['horizon_years']
    blended=(y*credit+cash_yield*cash+b['curve_yield_pct']/100*strip)/(credit+cash+strip)
    fee_fv=sum(b['annual_fee_usd']*(1+blended)**(years-n) for n in range(1,years+1))
    fv=60e6+credit*(1+y)**years+cash*(1+cash_yield)**years-fee_fv
    return {'classification':'conditional flat-carry 20Y scenario, not a forecast','terminal_usd':fv,'cagr':(fv/60e6)**(1/years)-1,
      'credit_reinvestment_eay':y,'cash_reinvestment_eay':cash_yield,'fee_opportunity_hurdle':blended,
      'fee_future_value_usd':fee_fv,'no_default_assumed':True,'put_payoff_in_base_case_usd':0.}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'results/reproduced');args=ap.parse_args()
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'checks/sha256_manifest.json').read_text())
    hash_checks={rel:checksum(ROOT/rel)==digest for rel,digest in manifest['files'].items()}
    if not all(hash_checks.values()):raise AssertionError('Input/code hash mismatch')
    d=read('data/frozen/module_nav_daily_usd.csv')
    assert len(d)==2504 and str(d.index[0].date())=='2016-09-30' and str(d.index[-1].date())=='2026-09-17'
    assert d.index.is_unique and d[list(CAP)].notna().all().all()
    residual=float((d.total-d[list(CAP)[:-1]].sum(axis=1)).abs().max())
    assert residual<.02
    expected=json.loads((ROOT/'checks/expected_metrics.json').read_text())
    baseline={k:stats(d[k],v) for k,v in CAP.items()}
    years=(d.index[-1]-d.index[0]).days/365.25;elapsed=(d.index-d.index[0]).days.to_numpy()/365.25
    fwd=forward_case();rate=fwd['cagr']
    drift=(60e6*(1+rate)**years/d.ficc.iloc[-1])**(1/years)
    d['ficc_calibrated']=d.ficc.to_numpy()*drift**elapsed
    d['hybrid_total']=d[['equities','commodities','crypto','fx']].sum(axis=1)+d.ficc_calibrated
    hybrid={'ficc':stats(d.ficc_calibrated,60e6),'total':stats(d.hybrid_total,100e6)}
    comparisons={}
    for label,actual,want in [('baseline',baseline,expected['baseline']),('hybrid',hybrid,expected['hybrid'])]:
        for sleeve,values in actual.items():
            for key in ['terminal_nav','cagr','sharpe','max_drawdown','annualized_vol']:
                delta=values[key]-want[sleeve][key]
                limit=1e-5 if key=='terminal_nav' else 1e-10
                comparisons[f'{label}.{sleeve}.{key}']={'absolute_error':abs(delta),'tolerance':limit,'pass':abs(delta)<limit}
    assert all(x['pass'] for x in comparisons.values())
    rebuilds={};issues={}
    for kind,module,sleeve in [('commodity',commodity_note,'commodities'),('crypto',crypto_note,'crypto')]:
        nav,iss=note_rebuild(kind,module);error=float((nav-d[sleeve]).abs().max())
        rebuilds[kind]={'method':'contract issue/roll/cashflow/mark engine re-executed from frozen causal index/vol/curve inputs','max_nav_difference_usd':error,'pass':error<.01}
        issues[kind]=iss;nav.to_csv(out/f'{kind}_rebuilt_nav.csv',index_label='date')
    nav,iss=equity_rebuild();error=float((nav-d.equities).abs().max())
    rebuilds['equities']={'method':'5Y floor/call-spread issue/roll/mark engine re-executed from frozen causal basket index,vol and official Fed curve','max_nav_difference_usd':error,'pass':error<.01}
    issues['equities']=iss;nav.to_csv(out/'equity_rebuilt_nav.csv',index_label='date')
    fc=read('data/ledgers/ficc_historical_components.csv')
    fn=fc[['strip_proxy_nav_usd','credit_proxy_nav_usd','vusxx_cash_nav_usd','protection_option_value_usd']].sum(axis=1)-fc.cumulative_annual_fee_paid_usd
    fn=fn.reindex(fn.index.union(d.index)).ffill().reindex(d.index)
    error=float((fn-d.ficc).abs().max())
    rebuilds['ficc']={'method':'frozen component accounting replay; six actual bond histories are NOT recreated','max_nav_difference_usd':error,'pass':error<.01}
    native=read('data/frozen/fx_native_nav.csv')
    fx=5e6*(1+native.source_daily_return.iloc[1:]).cumprod()
    fx=pd.concat([pd.Series([5e6],index=native.index[:1]),fx])
    fx=fx.reindex(fx.index.union(d.index)).sort_index().ffill().reindex(d.index)
    error=float((fx-d.fx).abs().max())
    rebuilds['fx']={'method':'native model-return compounding and union-calendar forward carry; factor estimation itself is not rerun without external data','max_nav_difference_usd':error,'pass':error<.01}
    attr=read('data/ledgers/fx_daily_attribution.csv')
    component_pnl=attr[['cash_pnl_usd','factor_pnl_usd','drag_pnl_usd']].sum().to_dict()
    assert abs(sum(component_pnl.values())-(d.fx.iloc[-1]-5e6))<.01
    assert all(v['pass'] for v in rebuilds.values()),rebuilds
    d.to_csv(out/'common_historical_and_hybrid_nav.csv',index_label='date',float_format='%.12f')
    result={'classification':'frozen research replay, not executable history','cutoff':'2026-09-17','baseline':baseline,'hybrid':hybrid,
      'hybrid_condition':'FICC drift is fitted with hindsight to forward-case terminal CAGR; other four histories unchanged. Not blind OOS or a forecast.',
      'forward_20y':fwd,'annual_gross_drift':drift,'weekly':{'historical':stats(weekly_marks(d.total),100e6,52),'hybrid':stats(weekly_marks(d.hybrid_total),100e6,52)},
      'engine_rebuild_checks':rebuilds,'metric_checks':comparisons,'module_sum_max_error_usd':residual,'fx_dollar_attribution':component_pnl,
      'all_hashes_pass':all(hash_checks.values()),'all_checks_pass':all(v['pass'] for v in rebuilds.values()) and all(v['pass'] for v in comparisons.values())}
    (out/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'issue_ledgers.json').write_text(json.dumps(issues,indent=2)+'\n')
    print(json.dumps({'all_checks_pass':result['all_checks_pass'],'history':baseline['total'],'hybrid':hybrid['total'],'rebuilds':rebuilds},indent=2))

if __name__=='__main__':main()
