# Team LARK — Scenario 2 research assets

Frozen inputs through **17 September 2026**. This repository supports the Team
LARK investment presentation. It contains computational code, derived research
datasets, model parameters, rebalance and contract ledgers, source provenance,
and an offline reproduction entry point. It places no orders.

## Run the frozen calculation

Python 3.11–3.14 is intended. The recorded acceptance run used Python 3.12.14,
NumPy 2.3.5 and pandas 2.2.3. No API key or Bloomberg terminal is required for
the offline calculation.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/reproduce.py --output results/local
```

The script checks the SHA-256 manifest, reconstructs the equity, commodity and
crypto note issue/roll/mark calculations, replays FICC component accounting and
FX native model returns, recomputes daily/weekly metrics, and checks them
against `checks/expected_metrics.json`. A successful run writes
`metrics.json`, reconstructed note NAVs, issue ledgers and the common
historical/hybrid NAV file. `results/accepted/` records the executed acceptance
run; it is an output snapshot, not an additional independent sample.

To work on the constrained commodity weighting code, also install
`requirements-research.txt`. Raw security data reconstruction is a separate
workflow described in [data acquisition](docs/DATA_ACQUISITION.md).

## Which calculation does this reproduce?

| Quantity | Definition | Published result |
|---|---|---:|
| Historical-model portfolio | Five frozen net USD NAVs added on a common calendar | CAGR 5.4263%; Sharpe 0.61965; MDD −15.5846%; terminal $169.293m |
| Conditional calibrated hybrid | Same four other sleeves; historical FICC path multiplied by a hindsight-fitted drift | CAGR 7.2567%; Sharpe 0.94932; MDD −14.4262%; terminal $200.965m |
| FICC forward flat-carry case | 20Y terminal cash-flow scenario with constant reinvestment and no base-case default | CAGR 5.50835%; terminal $175.343m |

The **7.26% hybrid is neither actual historical FICC performance nor a forecast**.
The script sets FICC's final value to the forward-case target CAGR by choosing
one drift multiplier after viewing the full sample. No other sleeve is uplifted.
The 5.51% forward case assumes the credit pool can compound at the current
weighted six-bond EAY of approximately 6.0661%, cash at 3.6823%, and no default
or downgrade. The 6.04% USD Funding Grid is a **borrowing cost**, not an asset
return. See [methods](docs/METHODS.md) and [limitations](docs/LIMITATIONS.md).

## Allocation and assets

| Sleeve | Initial capital | Files and computational engines |
|---|---:|---|
| FICC | $60m | `ficc_forward_20y.json`, bond/credit/contract ledgers, `ficc_protection.py` |
| Equities | $25m | Quarter targets/trades, PIT quality audit, `equity_selection.py`, `equity_quality.py`, `equity_rebalance.py`, equity note engines |
| Commodities | $5m | GLD/CPER/SLV/USO basket allocations, `commodity_rebalance.py`, `commodity_note.py` |
| Crypto | $5m | 3Y cap-100 note contracts, `crypto_note.py`; pre-IBIT BTC remains a proxy |
| FX/Rate | $5m | KR4 decision coefficients, native returns, dollar attribution, `kr4.py` |

The FICC 20Y design adopts $60m Treasury **redemption face**, costing about
$20.488m in the current fitted-curve model. Face is not additional invested
capital. The older internal $40m cap is retired for this design. CUSIP
912803HY2 redeems 15 August 2046, 33 days before the policy horizon; redemption
principal is to be ring-fenced for that bridge, with no additional principal
yield assumed. Six-issuer historical NAV uses a credit ETF proxy; it does not
reproduce those six bonds' actual histories.

## Reproducibility boundary

This package **fully reproduces the disclosed frozen calculation from the
included research inputs**. It does **not** claim independent reconstruction
from every original raw security record, a complete point-in-time universe,
dealer price history, actual option-implied volatility or signed issuer terms.

Raw third-party downloads, teammate private spreadsheets, competition PDF,
personal paths, API credentials, browser caches and private account data are
excluded. Derived output inclusion does not grant a license to redistribute
the originating providers' raw data. Current provider files may be revised;
a fresh download need not hash-match the captured version. Source URLs and
excluded-input checksums are in the acquisition manifest.

Code is research material supplied for review and reproduction. No broad
open-source or raw-data reuse license is implied. No Natixis endorsement or
issuer commitment is claimed. File identities and checksums are recorded in
`docs/source_provenance.json` and `checks/sha256_manifest.json`.
