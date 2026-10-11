from __future__ import annotations
import copy
import pandas as pd
from . import equity_rebalance as eq
FACTS={}
def facts_for(ticker, expanded=True):
    return FACTS.get(ticker,{}).get('facts',{})


def quality_features(ticker,cutoff,expanded=True):
    facts=facts_for(ticker,expanded);available=pd.Timestamp(cutoff)-pd.Timedelta(days=2)
    tags={'profit':['NetIncomeLoss','ProfitLoss'],
          'cfo':['NetCashProvidedByUsedInOperatingActivities','CashFlowsFromUsedInOperatingActivities'],
          'assets':['Assets']}
    table={}
    for key,names in tags.items():
        out=[]
        for ns in ('us-gaap','ifrs-full'):
            for tag in names:
                for unit,records in facts.get(ns,{}).get(tag,{}).get('units',{}).items():
                    if len(unit)!=3:continue
                    for rec in records:
                        if rec.get('form') not in ('20-F','20-F/A','10-K','10-K/A','40-F','40-F/A'):continue
                        if pd.Timestamp(rec.get('filed','2099-01-01'))>available:continue
                        end=pd.Timestamp(rec['end'])
                        if end>available or (available-end).days>550:continue
                        if key!='assets' and not 330<=(end-pd.Timestamp(rec.get('start',rec['end']))).days<=400:continue
                        out.append({**rec,'unit':unit,'tag':tag,'namespace':ns})
        table[key]=out
    joined=[]
    for a in table['assets']:
        if a['val']<=0:continue
        same=lambda x:x['end']==a['end'] and x['accn']==a['accn'] and x['unit']==a['unit']
        ps=[x for x in table['profit'] if same(x)];cs=[x for x in table['cfo'] if same(x)]
        if not ps or not cs:continue
        p=sorted(ps,key=lambda x:tags['profit'].index(x['tag']))[0];c=cs[0]
        joined.append({'end':a['end'],'filed':a['filed'],'accn':a['accn'],'unit':a['unit'],
          'profitability':p['val']/a['val'],'cashflow_assets':c['val']/a['val'],
          'cash_accrual_quality':(c['val']-p['val'])/a['val'],
          'profit_value':p['val'],'cfo_value':c['val'],'asset_value':a['val'],
          'profit_start':p.get('start'),'cfo_start':c.get('start'),
          'profit_tag':p['tag'],'cfo_tag':c['tag'],'assets_tag':a['tag']})
    return max(joined,key=lambda x:(x['end'],x['filed'])) if joined else None


def safe(tks,weights,row,uni):
    base=eq.target_weights_from_source(row,weights,False,uni)
    target=eq.target_weights_from_source(row,weights,'CASH_GRAB' in base,uni)
    return eq.constrain_core_caps(target,tks,uni)


def tilt(rows,cal,uni,expanded,accrual=False):
    out=copy.deepcopy(rows);audit=[];events=0
    for row in out:
        p=int(cal.searchsorted(row['workbook_date'],side='right')-1)-2
        if p<0:continue
        covered={t:q for t in row['tickers'] if (q:=quality_features(t,cal[p],expanded)) is not None}
        for t,q in covered.items():audit.append({'signal_date':str(row['workbook_date'].date()),'feature_date':str(cal[p].date()),'ticker':t,**q})
        if len(covered)<2:continue
        df=pd.DataFrame(covered).T
        keys=['profitability','cashflow_assets']+(['cash_accrual_quality'] if accrual else [])
        rank=sum(pd.to_numeric(df[k]).rank() for k in keys)/len(keys)
        weights={t:row['target_cashfix'][t]*(.75+.25*2*rank[t]/(len(covered)+1) if t in covered else 1) for t in row['tickers']}
        weights={t:.8*w/sum(weights.values()) for t,w in weights.items()}
        try:row['target_cashfix']=safe(row['tickers'],weights,row,uni);events+=1
        except ValueError:pass
    return out,audit,events

