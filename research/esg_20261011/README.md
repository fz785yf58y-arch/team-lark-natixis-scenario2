# Prospective public-source ESG evidence prototype

This research addendum supplements Team LARK's Scenario2 pitch. It was prepared11Oct2026 using a knowledge cutoff of **17Sep2026**. It was **not applied to the previously frozen historical backtest**. No performance uplift, issuer quote, issued contract, investment clearance or ESG certification is claimed.

Run with Python3 standard library only:

```sh
python3 run_screen.py --output screen_receipt.json
```

The program reads the archived `evidence.csv` and `config.json`; it does not fetch current data, generate new company facts, trade or alter holdings. The CSV preserves public URLs, release dates, entity/instrument scopes, source locators, material-risk triggers and gaps. Original copyrighted reports and personal local paths are intentionally excluded from this package.

A month-only date is an interval: availability uses month-end while freshness uses month-start. Both checks therefore use the conservative end for their purpose. A proposed548-day reporting freshness convention is a research operating choice, not an official competition requirement. Official published evidence after17Sep2026 is excluded, even if its measurement period was earlier. Current undated ratings cannot establish cutoff-date scores.

Dated-source eligibility is **not investment approval**. All reviewed entities remain on hold for additional exposure/renewals pending dated legal/sanctions, unresolved controversy, entity/product-scope and bank-parent reviews. Officially verified legal prohibitions warrant exclusion; material findings or evidence gaps warrant committee review and a freeze of additions/renewals. This prototype does not assert absence of controversies or automatically force liquidation.

The six entities are TSMC, Reliance, LG Energy Solution, Tencent, Alibaba and Meituan. Risks cover water/power continuity, fossil transition, mineral traceability/labour, data-centre energy, emissions methodology and courier safety. Public frameworks and targets are not proofs of safe outcomes. Multiple underlying companies do not diversify a common note-issuing bank.

Before adopting any changed investment selection, reprice participation/protection/costs and rerun comparable cash-flow/NAV risk checks. Original bank quote, final-term and legal-right gates remain open.
