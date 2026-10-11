from __future__ import annotations
import math, statistics
from datetime import date
from bisect import bisect_right
START=date(2016,9,30); CUTOFF=date(2026,9,17)
TENORS=(5,10,15); PROTECTION_BUFFER=.20; _VOL_CACHE={}


def add_year(d: date, n: int) -> date:
    try: return d.replace(year=d.year+n)
    except ValueError: return d.replace(year=d.year+n, day=28)


def zero_yield(p, t):
    b0,b1,b2,b3,t1,t2=p
    if t <= 1e-10: return b0+b1
    x1=t/t1; x2=t/t2
    a1=-math.expm1(-x1)/x1; a2=-math.expm1(-x2)/x2
    return b0+b1*a1+b2*(a1-math.exp(-x1))+b3*(a2-math.exp(-x2))


def zprice(p, t):
    return 1.0 if t <= 1e-10 else math.exp(-zero_yield(p,t)/100*t)


def yearfrac(d0,d1): return max(0.0,(d1-d0).days/365.25)


def normal_cdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))


def black76_put(spot, strike, expiry_years, sigma, df):
    if expiry_years <= 1e-10: return max(strike-spot,0.0)
    if sigma <= 1e-9:
        fwd=spot/df
        return df*max(strike-fwd,0.0)
    fwd=spot/df
    s=sigma*math.sqrt(expiry_years)
    d1=(math.log(fwd/strike)+0.5*s*s)/s
    d2=d1-s
    return max(0.0,df*(strike*normal_cdf(-d2)-fwd*normal_cdf(-d1)))


def rolling_vols(curve, dates, maturity, lookback_years=5):
    cache_key=(maturity,lookback_years,tuple(dates))
    if cache_key in _VOL_CACHE: return _VOL_CACHE[cache_key]
    all_days=sorted(d for d in curve if d <= CUTOFF)
    marks={d:zprice(curve[d],yearfrac(d,maturity)) for d in all_days if d<maturity}
    ret=[]
    for a,b in zip(all_days,all_days[1:]):
        if a in marks and b in marks and marks[a]>0 and marks[b]>0:
            ret.append((b,math.log(marks[b]/marks[a])))
    ret_days=[x for x,_ in ret]
    pref1=[0.0]; pref2=[0.0]
    for _,v in ret:
        pref1.append(pref1[-1]+v); pref2.append(pref2[-1]+v*v)
    result={}
    for d in dates:
        cutoff=add_year(d,-lookback_years)
        hi=bisect_right(ret_days,d); lo=bisect_right(ret_days,cutoff)
        n=hi-lo
        if n<100:
            lo=max(0,hi-1260); n=hi-lo
        if n<2: result[d]=0.18
        else:
            s1=pref1[hi]-pref1[lo]; s2=pref2[hi]-pref2[lo]
            var=max(0.0,(s2-s1*s1/n)/(n-1))
            result[d]=max(0.01,min(1.50,math.sqrt(var*252)))
    _VOL_CACHE[cache_key]=result
    return result


def option_schedule(curve, dates, maturity, budget, inception, tenors=TENORS, buffer=PROTECTION_BUFFER, lookback_years=5):
    p0=curve[inception]
    s0=zprice(p0,yearfrac(inception,maturity))
    vol_by_date=rolling_vols(curve,dates,maturity,lookback_years)
    vol0=vol_by_date[inception]
    legs=[]; unit_total=0.0
    for n in tenors:
        expiry=add_year(inception,n)
        t=yearfrac(inception,expiry)
        df=zprice(p0,t)
        fwd=s0/df
        k=(1.0-buffer)*fwd
        pv=black76_put(s0,k,t,vol0,df)
        legs.append({"expiry_years":n,"expiry_date":expiry.isoformat(),"maturity_date_underlier":maturity.isoformat(),"strike_price_per_1_face":k,"t0_forward_price_per_1_face":fwd,"t0_discount_factor":df,"t0_black76_vol_annualized":vol0,"premium_per_1_face":pv})
        unit_total+=pv
    notional=budget/unit_total if unit_total>0 else 0.0
    for leg in legs: leg["face_notional_usd"]=notional; leg["initial_model_premium_usd"]=notional*leg["premium_per_1_face"]
    return legs,notional,vol_by_date


def make_strip_component(curve, dates, cost, tenors, name):
    weights=[1.0/len(tenors)]*len(tenors)
    rungs=[]
    for tenor,w in zip(tenors,weights):
        maturity=add_year(START,tenor)
        unit=zprice(curve[START],yearfrac(START,maturity))
        rung_cost=cost*w
        rungs.append({"tenor":tenor,"initial_maturity":maturity,"face":rung_cost/unit,"price0":unit,"initial_value":rung_cost,"reset_log":[]})
    nav={}
    for d in dates:
        total=0.0
        for rung in rungs:
            while rung["initial_maturity"] <= d:
                maturity=rung["initial_maturity"]
                paydate=next((x for x in dates if x>=maturity),None)
                if paydate is None: break
                face=rung["face"]
                p=curve[paydate]
                newmat=add_year(paydate,20)
                price=zprice(p,yearfrac(paydate,newmat))
                rung["reset_log"].append({"roll_observation_date":paydate.isoformat(),"maturity_due":maturity.isoformat(),"proceeds_usd":face,"new_20y_zero_price_proxy":price,"new_maturity":newmat.isoformat()})
                rung["face"]=face/price
                rung["initial_maturity"]=newmat
            rem=yearfrac(d,rung["initial_maturity"])
            total+=rung["face"]*zprice(curve[d],rem)
        nav[d]=total
    ledger=[]
    for r in rungs:
        ledger.append({"initial_tenor_years":r["tenor"],"initial_maturity":add_year(START,r["tenor"]).isoformat(),"initial_market_value_usd":r["initial_value"],"initial_curve_face_usd":r["initial_value"]/r["price0"],"initial_price_per_1_face":r["price0"],"rolls":r["reset_log"]})
    return nav,ledger

