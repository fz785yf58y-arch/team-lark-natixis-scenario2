#!/usr/bin/env python3
"""Fetch official public sources to ignored local storage, never overwrite freeze."""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, re, urllib.request
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['fed-curve','treasury-2026','sec-companyfacts'],required=True)
    ap.add_argument('--output',type=Path,default=Path('downloads'));ap.add_argument('--cik');args=ap.parse_args()
    if args.source=='fed-curve':
        url='https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv';name='feds200628.csv';ua='Team-LARK-research-reproduction/1.0'
    elif args.source=='treasury-2026':
        url='https://home.treasury.gov/resource-center-data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026';name='treasury_2026.xml';ua='Team-LARK-research-reproduction/1.0'
    else:
        if not args.cik or not re.fullmatch(r'\d{1,10}',args.cik):ap.error('Supply the company CIK, digits only')
        ua=os.environ.get('SEC_USER_AGENT','')
        if not ua or '@' not in ua:ap.error('Set a contact-bearing SEC_USER_AGENT locally; do not commit it')
        cik=args.cik.zfill(10);url=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json';name=f'companyfacts_CIK{cik}.json'
    args.output.mkdir(parents=True,exist_ok=True);target=args.output/name
    if target.exists():raise FileExistsError(f'Preserve old source versions; choose a fresh output directory: {target}')
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':ua}),timeout=90) as response:payload=response.read()
    target.write_bytes(payload)
    record={'source_url':url,'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),'file':name,'changes_to_frozen_research':False}
    (args.output/(name+'.manifest.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':main()
