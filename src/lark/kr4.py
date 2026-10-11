from __future__ import annotations
import numpy as np
import pandas as pd

def first_in_period(ix,period="M"):
    keys=ix.to_period(period)
    return np.r_[True,keys[1:]!=keys[:-1]]

def base_weights(f,shrink=0.):
    out=pd.DataFrame(np.nan,index=f.index,columns=f.columns)
    decisions=pd.Series(f.index,index=f.index).resample('ME').last().dropna()
    for d in decisions:
        h=f.loc[d-pd.DateOffset(years=10):d]
        if (d-h.index[0]).days<365*9.9:continue
        C=h.cov().values;C=(1-shrink)*C+shrink*np.diag(np.diag(C))
        w=np.linalg.solve(C+np.eye(4)*1e-12,h.mean().values)
        w*=.10/max(np.sqrt(w@C@w*252),1e-10);out.loc[d]=w
    return out.ffill().fillna(0.)


def signal(unit,v):
    windows=v.get('windows',[63]);scores=[]
    for n in windows:
        sm=unit.rolling(n,min_periods=n).sum()
        if v.get('signal') in ['soft','hysteresis']:
            s=sm/(unit.rolling(n,min_periods=n).std()*np.sqrt(n))
        else:s=np.sign(sm)
        scores.append(s)
    z=pd.concat(scores,axis=1).mean(axis=1).fillna(0.)
    if v.get('signal')=='soft':return z.clip(-1,1)
    if v.get('signal')=='hysteresis':
        side=0.;rows=[]
        for val in z:
            if val>.5:side=1.
            elif val<-.5:side=-1.
            rows.append(side)
        return pd.Series(rows,index=z.index)
    return z


def risk(unit,v):
    s63=unit.rolling(63,min_periods=63).std()*np.sqrt(252)
    kind=v.get('risk','std63')
    if kind=='ewma':sd=unit.ewm(alpha=.06,adjust=False,min_periods=63).std()*np.sqrt(252)
    elif kind=='fastslow':
        sd=pd.concat([unit.rolling(20,min_periods=20).std(),unit.rolling(126,min_periods=126).std()],axis=1).max(axis=1)*np.sqrt(252)
    else:sd=s63
    g=.10/sd
    if kind=='inverse_variance':g=g**2
    return g.clip(upper=1).replace([np.inf,-np.inf],1.).fillna(0.)


def weights(f,v,base=None):
    if base is None:base=base_weights(f,v.get('shrink',0.))
    unit=(base.shift(1).fillna(0)*f).sum(axis=1)
    g=risk(unit,v)
    if v.get('signal')=='per_factor':
        # Time each factor's CONTRIBUTION to the base MV book. Raw factor
        # signs are arbitrary; multiplying MV weights by sign(raw F) is not
        # invariant to flipping a factor basis and is a different strategy.
        contributions=base.shift(1).fillna(0.)*f
        sides=pd.concat({n:np.sign(contributions.rolling(n,min_periods=n).sum()) for n in v.get('windows',[63,126,252])},axis=1)
        side=sum(sides[n] for n in v.get('windows',[63,126,252]))/len(v.get('windows',[63,126,252]))
        w=base*side.fillna(0.)
        oriented=(w.shift(1).fillna(0)*f).sum(axis=1)
        g=risk(oriented,v);w=w.mul(g,axis=0)
    else:w=base.mul(g*signal(unit,v),axis=0)
    cadence=v.get('rebalance','daily')
    if cadence!='daily':
        mask=first_in_period(w.index,'W-FRI' if cadence=='weekly' else 'M')
        w=w.where(pd.Series(mask,index=w.index),np.nan).ffill().fillna(0.)
    return w,g

