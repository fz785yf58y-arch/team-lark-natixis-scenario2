from __future__ import annotations
import math
from datetime import date
import numpy as np
import pandas as pd
from scipy.optimize import minimize
START=date(2016,9,30)
BASE=np.array([.5,.15,.15,.2]); ASSETS=['Gold','Copper','Silver','WTI']
LOW=np.array([.35,.10,.10,.10]); HIGH=np.array([.65,.25,.25,.25])


def bounded_simplex(raw):
    lo=-1.; hi=1.
    for _ in range(70):
        z=(lo+hi)/2; w=np.clip(raw-z,LOW,HIGH)
        if w.sum()>1: lo=z
        else: hi=z
    w=np.clip(raw-(lo+hi)/2,LOW,HIGH)
    assert abs(w.sum()-1)<1e-10
    return w


def create_index(name, rule, dates, prices, cost_bps=10., signal_extra_lag=0):
    px=np.array([[prices[a][d] for a in ASSETS] for d in dates])
    daily=np.zeros_like(px); daily[1:]=px[1:]/px[:-1]-1
    logrets=np.zeros_like(px); logrets[1:]=np.log(px[1:]/px[:-1])
    idx={dates[0]:1.}; costs={dates[0]:0.}; history=[]
    current=BASE.copy(); target=BASE.copy()
    for i in range(1,len(dates)):
        d0,d=dates[i-1],dates[i]
        quarter_change=(d.year,(d.month-1)//3)!=(d0.year,(d0.month-1)//3)
        initial=d==START
        cost=0.
        if quarter_change or initial:
            # Signal ends at the previous close. Executed before next session's return.
            j=max(0,i-1-signal_extra_lag)
            if j>=252:
                vol=logrets[max(1,j-251):j+1].std(axis=0,ddof=1)*np.sqrt(252)
                iv=1/np.maximum(vol,.05); iv/=iv.sum()
                ranks=[]
                for lookback in (63,126,252):
                    ret=px[j]/px[j-lookback]-1
                    ranks.append(pd.Series(ret).rank(method='average').to_numpy())
                rank=np.mean(ranks,axis=0); mom=rank/rank.sum()
                winners=np.argsort(rank,kind='stable')[-2:]
                top=np.zeros(4); top[winners]=.5
                minvar_strength=rule.get('minvar',0.)
                if minvar_strength:
                    cov=np.cov(logrets[max(1,j-251):j+1].T)*252
                    cov=.5*cov+.5*np.diag(np.diag(cov))
                    sol=minimize(lambda w:float(w@cov@w),BASE,method='SLSQP',
                        bounds=list(zip(LOW,HIGH)),constraints=[{'type':'eq','fun':lambda w:w.sum()-1}],
                        options={'ftol':1e-12,'maxiter':300})
                    assert sol.success,sol.message
                    mv=sol.x
                else: mv=BASE
                raw=(1-rule['iv']-rule['mom']-rule['top']-minvar_strength)*BASE+rule['iv']*iv+rule['mom']*mom+rule['top']*top+minvar_strength*mv
                target=bounded_simplex(raw)
            else: target=BASE.copy()
            if initial:
                # Match incumbent seeding convention; the start day's index return
                # occurs before buying the note and is not invested P&L.
                current=target.copy()
            if quarter_change:
                cost=cost_bps/10000.*np.abs(target-current).sum()
                current=target.copy()
            if d>=START:
                history.append({'date':d.isoformat(),'signal_last_date':dates[j].isoformat(),
                                **{a:float(target[k]) for k,a in enumerate(ASSETS)},
                                'full_l1_turnover':float(cost/(cost_bps/10000.)),'cost_fraction':float(cost)})
        gross=float(np.dot(current,daily[i])); idx[d]=idx[d0]*(1-cost)*(1+gross)
        current=current*(1+daily[i])/(1+gross); costs[d]=float(cost)
    return idx,costs,history

