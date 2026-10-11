#!/usr/bin/env python3
"""Small engine boundary checks; these do not validate return forecasts."""
from pathlib import Path
from datetime import date
import sys, json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from lark import commodity_note, crypto_note, ficc_protection, equity_rebalance, kr4, equity_quality

def main():
    checks={}
    checks['commodity_maturity_algebra']=all(abs(commodity_note.commodity_payoff_multiple(r,.45)-p)<1e-12 for r,p in [(-.3,.95),(-.5,.75),(-.8,.45),(0,1),(.2,1.09)])
    checks['crypto_principal_floor_and_cap']=crypto_note.crypto_payoff_multiple(-.9,.1,1.)==1. and crypto_note.crypto_payoff_multiple(3.,.1,1.)==1.1
    checks['put_expiry_intrinsic']=abs(ficc_protection.black76_put(.5,.8,0,.2,1)-.3)<1e-12
    checks['put_zero_vol_forward']=abs(ficc_protection.black76_put(.5,.8,5,0,.9)-.22)<1e-12
    curve={date(2016,9,30):(3.,-1.,.5,.5,1.,3.),date(2016,10,3):(3.1,-1.,.5,.5,1.,3.)}
    legs,face,_=ficc_protection.option_schedule(curve,list(curve),date(2036,9,30),1000.,date(2016,9,30))
    checks['staged_put_budget']=abs(sum(x['initial_model_premium_usd'] for x in legs)-1000.)<1e-8 and len(legs)==3
    checks['equity_caps_constants']=equity_rebalance.NAME_CAP==.08 and equity_rebalance.REGION_CAP==.35 and equity_rebalance.THEME_CAP==.40
    checks['equity_missing_quality_is_unknown']=equity_quality.quality_features('NO_DATA',pd.Timestamp('2020-01-01')) is None
    ix=pd.bdate_range('2000-01-01',periods=300);f=pd.DataFrame(np.random.default_rng(71).normal(0,.001,(300,4)),index=ix)
    w,g=kr4.weights(f,{'risk':'ewma','windows':[63]})
    checks['kr4_no_history_no_exposure']=float(w.abs().sum().sum())==0. and ((g>=0)&(g<=1)).all()
    assert all(checks.values()),checks
    print(json.dumps({'pass':True,'checks':{k:bool(v) for k,v in checks.items()},'classification':'synthetic boundary checks; not performance or loss probabilities'},indent=2))

if __name__=='__main__':main()
