# ESG review for our credit issuers

We prepared these notes on 11 October 2026 using information published by **17 September 2026**. They cover the six credit issuer groups in our proposal: TSMC, Reliance, LG Energy Solution, Tencent, Alibaba and Meituan.

We wanted the ESG review to address risks that could affect the credit case, rather than treating a renewable-energy theme as an ESG label. The evidence covers water and power continuity, fossil-fuel transition, mineral sourcing and labour, data-centre energy use, emissions reporting and courier safety.

This review is separate from our frozen historical backtest. We have not changed its holdings or NAVs, or attributed a return improvement to these checks.

## Run the check

From this directory, run:

```sh
python3 run_screen.py --output screen_receipt.json
```

The script uses Python's standard library and reads `evidence.csv` and `config.json`. The CSV records source URLs, publication dates, the entity or instrument covered, report locations, material risks and missing evidence. The script checks those records against our date rules. It does not fetch new company information or alter portfolio positions.

The saved result has nine evidence rows covering six groups. All nine meet the date checks. **All six groups remain `HOLD_NEW_PENDING_FULL_REVIEW`.** Passing the source-date check means the evidence is usable for review, not that the issuer has received investment approval.

## How we would use the review

We would review an issuer before a new investment or renewal, quarterly, and after a material event. A verified legal prohibition would exclude new exposure. An unresolved material finding or missing required evidence would pause additions and renewals until the committee reviews it. A flag alone would not automatically force an illiquid sale.

We still need dated legal and sanctions checks, controversy follow-up, confirmation that group evidence applies to the actual obligor, and a separate review of the note-issuing bank parent. Several underlying companies can still sit behind a claim on one bank. Public targets and policies are useful evidence, but do not prove remediation or safe outcomes. These notes are not an ESG certification, a green-bond classification, an issued contract or a bank quote.

## Dates and sources

Our proposed freshness limit is 548 days, roughly 18 months. It is our working convention, not a competition requirement. When a source only states its publication month, we use month-end for availability and month-start for freshness. This keeps both checks conservative. Reports published after 17 September 2026 are excluded even if they describe an earlier reporting period. An undated current rating cannot establish the score available at the cutoff.

The package contains the source links and our evidence records, rather than copies of copyrighted reports or personal file paths. Before a screen leads to a basket change, we would reprice participation, protection and fees, then rerun comparable cash-flow and NAV tests. Final issuer terms, legal rights and quotations are still outstanding.
