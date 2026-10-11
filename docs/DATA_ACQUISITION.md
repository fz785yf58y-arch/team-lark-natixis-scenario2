# Our data sources

The default reproduction run uses the research inputs already included in this repository. This page explains where the underlying data came from and what is still needed to rebuild the study from original security records.

## Files we include

We include modeled NAVs, target weights, simulated trade and note-issue records, derived basket index levels and lagged volatilities. These are enough to check our published calculations. They are not a replacement for a provider's raw adjusted-price feed, and should not be used to reconstruct or resell one.

We also include selected pre-cutoff Federal Reserve Svensson coefficients, with the official source URL and the captured file hash. They describe a fitted Treasury curve, rather than Treasury transaction prices. Our issuer-ID, rating and covenant summaries retain the date and scope of the supporting evidence. We do not redistribute rating-agency bulk data.

Original bulk downloads, private team workbooks and third-party reports are not part of the public package. A public URL does not by itself permit redistribution. Publishing our derived inputs does not grant rights to the original provider data, papers or prospectuses.

## Sources for a fresh rebuild

| Data | Source used | What needs checking |
|---|---|---|
| Equity and ETP prices, splits and dividends | Yahoo/OpenBB snapshots | Provider terms, local exchange dates, corporate actions and revisions |
| Historical stock pool | Official exchange exits and share records, company reports | Missing delistings, mergers, exit cash flows and the universe known at each date |
| Equity quality | SEC Companyfacts and Asian issuer filings | Units, fiscal end, accession and disclosure scope, with a two-day publication lag |
| Treasury discount curve | Federal Reserve nominal yield curve | Fitted coefficients and the last curve known at each valuation date |
| Commodity and crypto note discounting | US Treasury daily par-yield CSVs | Rates as decimals, cutoff at 17 September 2026 and the approximate semiannual bootstrap |
| BTC before IBIT | Coin Metrics community data and a captured Coinbase endpoint | Data rights and UTC timestamps. IBIT has no pre-2024 trading history |
| IBIT, GLD, CPER, SLV and USO | BlackRock, SPDR, USCF and iShares issuer pages | Exact ETF-share underlyings, inception dates and expenses |
| Credit return history | Captured Nasdaq/issuer CEMB prices and distributions | CEMB is a proxy. The six individual bond histories are still missing |
| VUSXX | Vanguard prospectus and distributions | Monthly distributions through August 2026, then a conservative latest-known extension to 17 September |
| KR4 factors | KR author archive at discount-bond-data.org | Data terms, source date convention and shifting returns to their outcome dates. The archive ends on 27 June 2025 |

`docs/acquisition_manifest.json` records the captured hashes of excluded numerical inputs where available. Providers may revise a file after we download it. A new download should therefore be recorded as a new version, rather than silently replacing the input behind the published result.

## Download helpers

The official-source helper supports these requests:

```bash
python scripts/fetch_public_sources.py --source fed-curve --output downloads
python scripts/fetch_public_sources.py --source treasury-2026 --output downloads
```

For SEC data, set a contact-bearing `SEC_USER_AGENT` environment variable and specify the company's CIK. Keep the contact value and any credentials out of the repository.

```bash
python scripts/fetch_public_sources.py --source sec-companyfacts --cik 0001046179 --output downloads
```

The helper saves the URL, UTC download time and SHA-256 alongside the files in the ignored `downloads` directory. Downloading a source does not alter the published inputs. Yahoo, Nasdaq and the author-factor datasets need to be obtained under their respective terms, so the helper does not automatically download or republish them.

## What we still need

The repository includes the selection, quarterly trading, commodity weighting, note valuation, FICC protection and KR4 timing functions. A fresh run from raw security data also needs the original provider files, the original quarterly-shortlist export and a complete point-in-time stock pool, with the necessary access rights.

The saved quarterly targets let readers reproduce the basket we tested. They cannot show which missing or delisted stocks might have entered the shortlist. Completing that historical pool is a separate piece of work.
