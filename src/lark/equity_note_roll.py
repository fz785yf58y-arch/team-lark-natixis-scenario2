from __future__ import annotations
import pandas as pd
from . import equity_note as note

def price_note(underlier,dates,vol):
    curves=note.curve_helpers.read_curve(); curve_dates=sorted(curves)
    def discount(day,tenor):
        from bisect import bisect_right
        j=bisect_right(curve_dates,day)-1
        if j<0: raise ValueError("Missing prior curve")
        return note.curve_helpers.zprice(curves[curve_dates[j]],tenor)
    wealth=1.0; face=None; participation=None; reference=None; maturity=None
    marks=[]; issues=[]
    for dt in dates:
        day=dt.date(); current=float(underlier.loc[dt]); sigma=float(vol.loc[dt])
        if maturity is not None and day>=maturity:
            payoff=.90+participation*min(max(current/reference-1.0,0.0),1.0)
            wealth=face*payoff; face=None
        if face is None:
            maturity=note.curve_helpers.add_year(day,5)
            tenor=(maturity-day).days/365.25; df=discount(day,tenor)
            spread=note.call(1.,1.,df,sigma,tenor)-note.call(1.,2.,df,sigma,tenor)
            participation=max(0.0,(1.0-.005-.90*df)/spread)
            face=wealth; reference=current
            issues.append({"issue_date":str(day),"maturity":str(maturity),"participation":participation,
                           "discount_factor":df,"shared_vol_proxy":sigma,"par_budget_price":.995})
        tenor=max(0.0,(maturity-day).days/365.25); df=discount(day,tenor); ratio=current/reference
        spread=note.call(ratio,1.,df,sigma,tenor)-note.call(ratio,2.,df,sigma,tenor)
        marks.append(face*(.90*df+participation*spread))
    return pd.Series(marks,index=dates,name="nav_multiple"),issues

