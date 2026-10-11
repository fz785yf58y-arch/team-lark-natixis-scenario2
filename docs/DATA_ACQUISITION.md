# Sources, permissions and independent rebuilding

The default run needs only the included research-derived input snapshots.
Original third-party bulk downloads are not in this public repository. Public
access alone is not a redistribution license. No repository license is granted
to original provider data, papers, issuer prospectuses or teammate workbooks.

## Data included

1. Authored model NAVs, strategy target weights, simulated trade/issue ledgers,
   derived reference-basket index levels and causal volatilities. These permit
   verification of the team's published calculations, not rebranding of a
   provider's raw adjusted-price feed. Do not reconstruct/resell provider
   prices from the derived index files.
2. Selected official Federal Reserve Svensson coefficients dated before the
   cutoff. The original US-government source URL and captured file SHA-256 are
   recorded. This is a fitted discount model, not Treasury transaction data.
3. Authored issuer-ID/rating/covenant summaries and model terms. A rating's
   object scope and evidence date remain part of the record; no rating agency
   bulk data is redistributed.

## Raw sources to retrieve separately

| Area | Source | Independent rebuild requirement |
|---|---|---|
| Equity/ETP prices, splits, dividends | Original Yahoo/OpenBB snapshots | Review provider terms, obtain locally, retain local exchange dates and corporate actions; snapshots may revise |
| Historical equity pool | Official exchange exits/shares and company reports | Complete delistings/mergers/exit cash flows and announcement-time universe; current pool is partial |
| Equity quality | SEC Companyfacts and Asian issuer filings | Match units, fiscal end and accession; filed date plus two-day availability lag; preserve source scope |
| Treasury curve | Federal Reserve nominal yield curve | Official fitted coefficients, with causal last-known-date handling |
| Commodity/Crypto note discount | US Treasury daily par-yield CSVs | Rates in decimals, dated to17Sep2026; approximate semiannual bootstrap |
| BTC before IBIT | Coin Metrics community data; captured Coinbase endpoint | Verify license and UTC clock; no complete pre2024 IBIT history exists |
| IBIT/GLD/CPER/SLV/USO identities | BlackRock, SPDR, USCF and iShares issuer pages | Keep exact ETF-share contractual underlyings, fees and inception dates |
| Credit history | Captured Nasdaq/issuer CEMB data and distributions | Proxy only; actual six individual bond histories remain missing |
| VUSXX | Vanguard prospectus and distributions | Monthly distributions throughAug2026; conservative latest-known extension to17Sep2026 |
| KR4 factors | KR author archive, discount-bond-data.org | Review terms, preserve original date convention then shift returns to outcome date; original archive ends27Jun2025 |

`docs/acquisition_manifest.json` lists captured hashes of excluded numerical
inputs where available. A newly fetched current version is not automatically
the captured version and must not silently replace it in the published result.

## Official-source download helper

```bash
python scripts/fetch_public_sources.py --source fed-curve --output downloads
python scripts/fetch_public_sources.py --source treasury-2026 --output downloads
```

SEC requests require a contact-bearing `SEC_USER_AGENT` environment variable
and an explicit CIK; do not commit that environment variable or a credential:

```bash
python scripts/fetch_public_sources.py --source sec-companyfacts --cik 0001046179 --output downloads
```

The helper records URL, UTC retrieval timestamp and SHA-256 in the ignored
downloads directory. It downloads source material only; it does not mutate
frozen input datasets or claim a complete independent-security rebuild. Raw
Yahoo, Nasdaq and author-factor datasets require acquisition in line with
their terms and are intentionally not auto-downloaded or republished here.

## What remains before a full raw-input re-run?

The computational functions for selection, quarter trading, commodity weights,
note budget valuation, staged FICC protection and KR4 timing are included.
Their inputs are explicit. A full new end-to-end raw-security run still needs
the captured raw provider files, original quarterly-shortlist export, complete
PIT pool and current rights/access. The included frozen quarter targets verify
the adopted portfolio, but they cannot independently establish that absent
historical securities would not have been selected. This limitation is not
fixed by rerunning the frozen NAVs.
