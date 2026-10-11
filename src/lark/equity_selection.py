from __future__ import annotations
import copy, math
import numpy as np
import pandas as pd
from . import equity_rebalance as eq

def safe_projection(tickers, weights, row, universe):
    raw=eq.target_weights_from_source(row,weights,False,universe)
    target=eq.target_weights_from_source(row,weights,'CASH_GRAB' in raw,universe)
    return eq.constrain_core_caps(target,tickers,universe)

def features(prices,returns,p,universe):
    # Quarter signal uses two previous U.S. sessions, followed by next-session
    # execution. Latest month is excluded from momentum; six months may be
    # used alone until twelve-month history becomes available.
    obs=p-2
    if obs<147:return {},None
    out={}
    for tk in prices.columns:
        if tk in eq.SAT:continue
        series=prices[tk]
        if not np.isfinite(series.iloc[obs-147]) or not np.isfinite(series.iloc[obs]):continue
        vol=float(returns[tk].iloc[obs-125:obs+1].std(ddof=1)*math.sqrt(252))
        if vol<.02 or not np.isfinite(vol):continue
        m6=float(series.iloc[obs-21]/series.iloc[obs-147]-1)
        m12=(float(series.iloc[obs-21]/series.iloc[obs-273]-1)
             if obs>=273 and np.isfinite(series.iloc[obs-273]) else None)
        mom=m6 if m12 is None else .5*(m6+m12)
        out[tk]={'momentum6_skip1':m6,'momentum12_skip1':m12,'vol126':vol,
                 'risk_adjusted_momentum':mom/vol,'theme':eq.canon_theme(universe,tk)}
    return out,obs


def schedule_for_rule(rule,schedules,cal,prices,returns,universe):
    rows=copy.deepcopy(schedules); features_log=[]; audit=[]
    for row in rows:
        p=int(cal.searchsorted(row['workbook_date'],side='right')-1)
        feat,obs=features(prices,returns,p,universe)
        original=list(row['tickers'])
        selectable=[t for t in original if t in feat]
        # No imported pre-2016 history and no invented features. Keep baseline
        # target until every original core name has a valid signal.
        selected=original; target=dict(row['target_cashfix']); fallback='baseline_warmup_or_incomplete_core_history'
        if len(selectable)==len(original):
            fallback=None
            if rule.startswith('union_'):
                selected=[]
                for theme,n in [('SEMI',5),('INTERNET',4),('AI',3),('NEW_ENERGY',2),('IT_SERVICES',1)]:
                    eligible=sorted([t for t,f in feat.items() if f['theme']==theme],
                        key=lambda t:(-feat[t]['risk_adjusted_momentum'],t))
                    selected+=eligible[:n]
                if len(selected)!=15:
                    selected=original; fallback='insufficient_union_theme_history'
            elif rule=='shortlist_riskmom_prune3_invvol':
                selected=sorted(original,key=lambda t:(-feat[t]['risk_adjusted_momentum'],t))[:12]
            while True:
                if fallback:
                    target=dict(row['target_cashfix']);break
                if rule=='shortlist_riskmom_tilt':
                    x=np.array([feat[t]['risk_adjusted_momentum'] for t in selected]);
                    z=(x-x.mean())/max(x.std(ddof=0),1e-12);z=np.clip(z,-3,3)
                    score=np.where(z>=0,1+z,1/(1-z))
                    raw={t:row['target_base'][t]*float(score[j]) for j,t in enumerate(selected)}
                elif rule.endswith('invvol') or rule=='shortlist_inverse_vol':
                    raw={t:1/feat[t]['vol126'] for t in selected}
                else:raw={t:1. for t in selected}
                total=sum(raw.values());weights={t:.8*w/total for t,w in raw.items()}
                try:
                    target=safe_projection(selected,weights,row,universe);break
                except (ValueError,AssertionError):
                    # Removing a name cannot make caps disappear. Add the next
                    # highest-ranked original eligible name until feasible.
                    extra=[t for t in sorted(original,key=lambda t:(-feat[t]['risk_adjusted_momentum'],t)) if t not in selected]
                    if extra:selected.append(extra[0])
                    else:
                        target=dict(row['target_cashfix']);selected=original;fallback='infeasible_caps_baseline_fallback';break
        row['target_cashfix']=target;row['tickers']=selected
        actual=eq.actual_cap_breaches(target,universe)
        if actual:raise AssertionError((rule,row['workbook_date'],actual))
        audit.append({'rule':rule,'signal_date':str(row['workbook_date'].date()),
            'features_through':str(cal[obs].date()) if obs is not None else None,
            'fallback':fallback,'selected_core_names':len(selected),
            'weight_sum':sum(target.values()),'target_cap_breaches':';'.join(actual)})
        for t,f in feat.items():features_log.append({'rule':rule,'signal_date':str(row['workbook_date'].date()),
             'features_through':str(cal[obs].date()),'ticker':t,**f,'selected':t in selected,
             'within_quarter_shortlist':t in original,'target_weight':target.get(t,0)})
    return rows,audit,features_log

