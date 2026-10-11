from __future__ import annotations
import numpy as np
import pandas as pd
START=pd.Timestamp('2016-09-30'); INITIAL_CAPITAL_USD=25_000_000.
NAME_CAP=.08; REGION_CAP=.35; THEME_CAP=.40; DRIFT_BAND=.02
SAT={'9983.T':.20/3,'INDA':.20/3,'GRAB':.20/3}


def target_weights_from_source(schedule, core_weights, cash_cap_fix=False, universe=None):
    w=dict(core_weights)
    # Team targets use a fixed 20% satellite: three equal slots. Before GRAB
    # begins trading, its slot is recorded as USD cash.
    w['9983.T']=SAT['9983.T']; w['INDA']=SAT['INDA']
    if schedule['cash_satellite']>0 or schedule['workbook_date'] < pd.Timestamp('2021-12-02'):
        w['CASH_GRAB']=SAT['GRAB']
    else: w['GRAB']=SAT['GRAB']
    if abs(sum(w.values())-1.0)>0.00015:
        raise AssertionError(f'target weight sum {sum(w.values())} on {schedule["workbook_date"]}')
    if cash_cap_fix and 'CASH_GRAB' in w:
        excess=w['CASH_GRAB']-0.05
        if excess<=0: raise AssertionError('cash cap candidate expected excess cash')
        w['CASH_GRAB']=0.05
        # Reinvest in proportion to every existing listed portfolio holding
        # (core plus already-listed 9983.T and INDA), subject to name/region/theme caps.
        active=[tk for tk in w if not tk.startswith('CASH_') and not tk.startswith('UNPRICED_')]
        theme={tk:universe.get(tk,{}).get('theme','') for tk in active}
        region={tk:universe.get(tk,{}).get('region','') for tk in active}
        theme_exp={}; region_exp={}
        for tk in active:
            th=theme[tk]; rg=region[tk]
            if th and not th.startswith('SATELLITE'): theme_exp[th]=theme_exp.get(th,0.0)+w[tk]
            if rg: region_exp[rg]=region_exp.get(rg,0.0)+w[tk]
        remaining=excess
        for _ in range(100):
            if remaining<1e-12: break
            eligible=[]
            for tk in active:
                th=theme[tk]; rg=region[tk]
                th_room=(THEME_CAP-theme_exp.get(th,0.0)) if th and not th.startswith('SATELLITE') else remaining
                rg_room=(REGION_CAP-region_exp.get(rg,0.0)) if rg else remaining
                if min(NAME_CAP-w[tk],th_room,rg_room)>1e-12: eligible.append(tk)
            if not eligible: break
            denom=sum(max(w[tk],1e-5) for tk in eligible)
            proposed={tk:remaining*max(w[tk],1e-5)/denom for tk in eligible}
            added=0.0
            for tk in eligible:
                th=theme[tk]; rg=region[tk]
                th_room=(THEME_CAP-theme_exp.get(th,0.0)) if th and not th.startswith('SATELLITE') else remaining
                rg_room=(REGION_CAP-region_exp.get(rg,0.0)) if rg else remaining
                room=max(0.0,min(NAME_CAP-w[tk],th_room,rg_room))
                inc=min(room,proposed[tk]); w[tk]+=inc; added+=inc
                if th and not th.startswith('SATELLITE'): theme_exp[th]=theme_exp.get(th,0.0)+inc
                if rg: region_exp[rg]=region_exp.get(rg,0.0)+inc
            remaining-=added
            if added<1e-12: break
        if remaining>1e-7:
            raise ValueError(f'Unable to allocate cash excess within caps: remaining={remaining:.8f} on {schedule["workbook_date"].date()}')
    if abs(sum(w.values())-1)>2e-5: raise AssertionError('cash-fix candidate does not sum to 1')
    return w


def constrain_core_caps(target, core_tickers, universe):
    """Project candidate core target back under sleeve name/region/theme caps."""
    out=dict(target); core=list(core_tickers); core_total=sum(out[t] for t in core)
    raw={t:out[t] for t in core}; x=dict(raw)
    fixed={t:w for t,w in out.items() if t not in core}
    def region(t): return universe.get(t,{}).get('region','')
    def theme(t): return universe.get(t,{}).get('theme','')
    fixed_region={}; fixed_theme={}
    for tk,w in fixed.items():
        if tk.startswith('CASH_') or tk.startswith('UNPRICED_'): continue
        rg=region(tk); th=theme(tk)
        if rg: fixed_region[rg]=fixed_region.get(rg,0.0)+w
        if th and not th.startswith('SATELLITE'): fixed_theme[th]=fixed_theme.get(th,0.0)+w
    for _ in range(100):
        for t in core: x[t]=min(x[t],NAME_CAP)
        for rg in set(region(t) for t in core):
            grp=[t for t in core if region(t)==rg]
            allowed=REGION_CAP-fixed_region.get(rg,0.0); total=sum(x[t] for t in grp)
            if total>allowed+1e-12 and total>0:
                scale=max(0.0,allowed/total)
                for t in grp: x[t]*=scale
        for th in set(theme(t) for t in core):
            if not th or th.startswith('SATELLITE'): continue
            grp=[t for t in core if theme(t)==th]
            allowed=THEME_CAP-fixed_theme.get(th,0.0); total=sum(x[t] for t in grp)
            if total>allowed+1e-12 and total>0:
                scale=max(0.0,allowed/total)
                for t in grp: x[t]*=scale
        deficit=core_total-sum(x.values())
        if deficit<=1e-10: break
        eligible=[]
        for t in core:
            rg=region(t); th=theme(t)
            region_room=REGION_CAP-fixed_region.get(rg,0.0)-sum(x[a] for a in core if region(a)==rg)
            theme_room=(THEME_CAP-fixed_theme.get(th,0.0)-sum(x[a] for a in core if theme(a)==th)) if th and not th.startswith('SATELLITE') else deficit
            if min(NAME_CAP-x[t],region_room,theme_room)>1e-12: eligible.append(t)
        if not eligible: break
        denom=sum(max(raw[t],1e-5) for t in eligible)
        proposed={t:deficit*max(raw[t],1e-5)/denom for t in eligible}
        added=0.0
        for t in eligible:
            rg=region(t); th=theme(t)
            region_room=REGION_CAP-fixed_region.get(rg,0.0)-sum(x[a] for a in core if region(a)==rg)
            theme_room=(THEME_CAP-fixed_theme.get(th,0.0)-sum(x[a] for a in core if theme(a)==th)) if th and not th.startswith('SATELLITE') else deficit
            room=max(0.0,min(NAME_CAP-x[t],region_room,theme_room))
            inc=min(room,proposed[t]); x[t]+=inc; added+=inc
        if added<1e-12: break
    if abs(sum(x.values())-core_total)>1e-7:
        raise ValueError(f"cannot project target to caps while preserving core weight: shortfall={core_total-sum(x.values()):.8f}")
    out.update(x)
    return out


def lagged_trade_dates(cal, schedules, lag):
    schedule_dates=[]
    for row in schedules:
        pos=cal.searchsorted(row['workbook_date'],side='right')-1
        if pos<0: continue
        if lag and row['workbook_date']>START: pos=min(pos+1,len(cal)-1)
        schedule_dates.append((cal[pos],row))
    return schedule_dates


def turnover(pre, post):
    keys=set(pre)|set(post)
    return 0.5*sum(abs(float(post.get(k,0.0))-float(pre.get(k,0.0))) for k in keys)


def canon_region(universe, ticker):
    value=universe.get(ticker,{}).get('region','')
    return {'SEA':'South-East Asia','South East Asia':'South-East Asia','South-East Asia':'South-East Asia'}.get(value,value)


def canon_theme(universe, ticker):
    x=universe.get(ticker,{}).get('theme','').upper().replace(' ','_').replace('-','_')
    if 'SEMI' in x or 'HARDWARE' in x: return 'SEMI'
    if 'INTERNET' in x or 'PAYMENT' in x: return 'INTERNET'
    if x=='AI' or 'CLOUD' in x or 'AUTOMATION' in x: return 'AI'
    if 'ENERGY' in x: return 'NEW_ENERGY'
    if 'IT_SERVICE' in x or 'ITSERV' in x or 'SERVICES' in x or 'DIGITAL_INFRA' in x: return 'IT_SERVICES'
    return x


def actual_cap_breaches(weights, universe):
    """Return cap breaches using current close weights and the workbook groupings."""
    assets={k:v for k,v in weights.items() if not k.startswith(('CASH_','UNPRICED_'))}
    cash=sum(v for k,v in weights.items() if k.startswith(('CASH_','UNPRICED_')))
    region_exp={}; theme_exp={}
    for ticker,w in assets.items():
        region=canon_region(universe,ticker)
        theme=canon_theme(universe,ticker)
        if region: region_exp[region]=region_exp.get(region,0.0)+w
        if theme and not theme.startswith('SATELLITE'):
            theme_exp[theme]=theme_exp.get(theme,0.0)+w
    result=[]
    if cash>0.05+1e-10: result.append('cash')
    if max(assets.values() or [0.0])>NAME_CAP+1e-10: result.append('single_security')
    if max(region_exp.values() or [0.0])>REGION_CAP+1e-10: result.append('region')
    if max(theme_exp.values() or [0.0])>THEME_CAP+1e-10: result.append('theme')
    return result


def run_candidate_simple(name, cal, prices, returns, schedules, candidate, cost_rate, universe):
    """Correct NAV/quantity simulation with instrument units; supports buffers and unpriced cash."""
    trade_map=dict(lagged_trade_dates(cal,schedules,candidate['lag']))
    nav=1.0; units={}; nav_rows=[]; ledger=[]; holdings=[]
    latest_row=None; pending_daily_repair=False; pending_breaches=[]

    def current_weights(dt):
        if not units or not nav: return {}
        out={}
        for tk,qty in units.items():
            if tk.startswith(('CASH_','UNPRICED_')): value=qty
            else:
                p=prices.loc[dt,tk] if tk in prices.columns else np.nan
                value=qty*p if np.isfinite(p) else qty
            out[tk]=value/nav
        return out

    def target_at_close(raw_target, dt):
        target={}
        for tk,w in raw_target.items():
            p=prices.loc[dt,tk] if tk in prices.columns else np.nan
            if tk.startswith('CASH_'): target[tk]=w
            elif not np.isfinite(p): target['UNPRICED_'+tk]=target.get('UNPRICED_'+tk,0)+w
            else: target[tk]=target.get(tk,0)+w
        return target

    for i,dt in enumerate(cal):
        # Mark prior close units to current close using total-return price levels.
        if i>0 and units:
            nav=0.0
            for tk,qty in units.items():
                if tk.startswith('CASH_') or tk.startswith('UNPRICED_'):
                    nav+=qty
                else:
                    p=prices.loc[dt,tk] if tk in prices.columns else np.nan
                    if not np.isfinite(p):
                        nav+=qty # treated as zero-return cash proxy; never spend the proxy until rebalance
                    else:
                        nav+=qty*p
        scheduled=dt in trade_map
        repair_due=bool(candidate.get('daily_cap') and pending_daily_repair and not scheduled)
        repair_signal_breaches=list(pending_breaches) if repair_due else []
        do_review=scheduled or repair_due
        if scheduled:
            row=trade_map[dt]
            latest_row=row
        elif repair_due:
            row=latest_row
        else:
            row=None
        if do_review and row is not None:
            if candidate.get('shrink_90_10'):
                raw_target=dict(row['target_90_10_cashfix'] if candidate['cash_fix'] else row['target_90_10_base'])
            else:
                raw_target=dict(row['target_cashfix'] if candidate['cash_fix'] else row['target_base'])
            target=target_at_close(raw_target,dt)
            pre=current_weights(dt)
            if not units:
                do_trade=True; trigger='initial'; to=1.0; total_notional=1.0
            else:
                if repair_due:
                    do_trade=True; trigger='daily_cap_repair_next_session'
                elif scheduled:
                    drift=max([abs(pre.get(k,0.0)-target.get(k,0.0)) for k in set(pre)|set(target)] or [0.0])
                    changed=set(pre)!=set(target)
                    do_trade=(not candidate['band']) or changed or drift>DRIFT_BAND+1e-12
                    trigger='quarterly_rebalance_drift_or_constituent_change' if do_trade else 'quarterly_within_2pp_no_trade'
                else:
                    do_trade=False; trigger='no_trade'
                to=turnover(pre,target) if do_trade else 0.0
                total_notional=2.0*to if do_trade else 0.0
            if do_trade:
                # Charge 10bp to every dollar of gross purchases and sales.
                # Initial seed is all buys only; later trades have equal gross
                # buys/sells, with 0.5*L1 on each side and L1 total notional.
                cost=total_notional*cost_rate
                nav*=1-cost
                units={}
                for tk,w in target.items():
                    if tk.startswith('CASH_') or tk.startswith('UNPRICED_'):
                        units[tk]=nav*w
                    else:
                        p=prices.loc[dt,tk]
                        units[tk]=nav*w/p
            else:
                cost=0.0
            for tk in sorted(set(pre)|set(target)):
                ledger.append({'candidate':name,'trade_date':dt.date().isoformat(),
                    'workbook_date':row['workbook_date'].date().isoformat(),'ticker':tk,
                    'pre_trade_weight':pre.get(tk,0.0),'target_weight':target.get(tk,0.0),
                    'trade_weight':(target.get(tk,0.0)-pre.get(tk,0.0)) if do_trade else 0.0,
                    'one_way_turnover_each_side':to,'gross_buy_sell_notional':total_notional,
                    'cost_bps_each_buy_or_sell':cost_rate*10000.,
                    'cost_fraction_nav':cost,'nav_usd_after_trade':nav*INITIAL_CAPITAL_USD,
                    'trade_trigger':trigger,'trade_executed':bool(do_trade),
                    'signal_date':(cal[i-1].date().isoformat() if repair_due and i>0 else None),
                    'signal_breaches':';'.join(repair_signal_breaches),
                    'execution_clock':'close_of_trade_date_after_prior_session_close_signal' if repair_due else 'close_of_trade_date'})
        nav_rows.append((dt,nav))
        weights_at_close=current_weights(dt)
        if candidate.get('daily_cap'):
            # The signal is computed only after today's close has marked all positions.
            # A detected breach is queued for execution at the next U.S. session close.
            pending_breaches=actual_cap_breaches(weights_at_close,universe)
            pending_daily_repair=bool(pending_breaches)
        if nav:
            for tk,qty in units.items():
                if tk.startswith('CASH_') or tk.startswith('UNPRICED_'): value=qty
                else:
                    p=prices.loc[dt,tk]
                    value=qty*p if np.isfinite(p) else qty
                holdings.append({'date':dt.date().isoformat(),'candidate':name,'ticker':tk,
                                 'weight':value/nav,'market_value_usd':value*INITIAL_CAPITAL_USD})
    s=pd.Series(dict(nav_rows),dtype=float).sort_index()
    return s/s.iloc[0],ledger,holdings

