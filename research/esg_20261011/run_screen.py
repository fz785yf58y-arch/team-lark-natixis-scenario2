"""Classify archived public ESG evidence. No internet, trading or backtest mutation."""
import argparse,calendar,csv,hashlib,json
from datetime import date
from pathlib import Path

def classify(row,config):
    cutoff=date.fromisoformat(config['cutoff']); issues=[]
    for field in config['minimum_fields']:
        if not row.get(field): issues.append('missing_'+field)
    raw=row.get('publication_date','')
    try:
        if len(raw)==7:
            y,m=map(int,raw.split('-'))
            availability=date(y,m,calendar.monthrange(y,m)[1])
            freshness=date(y,m,1)
        else:
            availability=freshness=date.fromisoformat(raw)
        if availability>cutoff: issues.append('post_cutoff_or_interval_not_fully_pre_cutoff')
        if (cutoff-freshness).days>config['freshness_max_days']: issues.append('stale_reporting')
    except ValueError:
        issues.append('unverified_publication_date')
    return {'id':row['id'],'entity':row['entity'],'dated_evidence_eligible':not issues,
            'evidence_issues':issues,'investment_status':'HOLD_NEW_PENDING_FULL_REVIEW',
            'remaining_checks':['dated legal and sanctions review','unresolved official controversy review',
                                'entity/product scope and bank-parent check'],
            'rationale':'Dated disclosure is an input, not investment clearance.'}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='screen_receipt.json')
    args=parser.parse_args(); base=Path(__file__).resolve().parent
    config=json.loads((base/'config.json').read_text())
    rows=list(csv.DictReader((base/'evidence.csv').open(newline='')))
    results=[classify(r,config) for r in rows]
    receipt={'classification':config['classification'],'cutoff':config['cutoff'],
             'evidence_rows':len(results),'entity_count':len({r['entity'] for r in rows}),
             'eligible_dated_rows':sum(r['dated_evidence_eligible'] for r in results),
             'all_entity_approvals':'UNRESOLVED; no automatic pass',
             'sha256_inputs':{f:hashlib.sha256((base/f).read_bytes()).hexdigest()
                              for f in ['evidence.csv','config.json']},'results':results}
    Path(args.output).write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['evidence_rows','entity_count','eligible_dated_rows','all_entity_approvals']}))
if __name__=='__main__': main()
