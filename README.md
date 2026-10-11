# Team LARK | Natixis Investment Strategy Challenge 2026

This repository contains the research behind our Scenario 2 proposal for NKE Private Wealth. We use a USD 100m allocation and a 20-year investment horizon, with market data ending on **17 September 2026**.

Our allocation puts most of the capital into FICC, with smaller allocations to Asian equities, commodities, crypto and FX/Rate. The code, model inputs and portfolio records are here so readers can follow our calculations and reproduce the figures in our presentation.

## Our allocation

| Module | Initial capital | Main research files |
|---|---:|---|
| FICC | $60m | `ficc_forward_20y.json`, bond and contract ledgers, `ficc_protection.py` |
| Equities | $25m | Quarterly targets and trades, `equity_selection.py`, `equity_quality.py`, `equity_rebalance.py`, equity note engines |
| Commodities | $5m | GLD/CPER/SLV/USO basket, `commodity_rebalance.py`, `commodity_note.py` |
| Crypto | $5m | Three-year notes with capped upside, `crypto_note.py` |
| FX/Rate | $5m | KR4 factor weights, returns and attribution, `kr4.py` |

For FICC, the Treasury component targets $60m of redemption principal. Its modeled purchase cost is about $20.488m, so the face amount is not another $60m of invested capital. The earlier $40m limit was an internal design constraint that we retired for this version. CUSIP 912803HY2 matures on 15 August 2046, 33 days before the policy horizon. In the model, we assume the redemption principal is held for that interval with no extra return. The actual bridge arrangement still needs confirmation.

## Reading the results

We show three calculations because they answer different questions:

| Calculation | What it shows | Result |
|---|---|---:|
| Historical-model portfolio | The five modeled USD NAVs combined on the same calendar | CAGR 5.4263%, Sharpe 0.61965, maximum drawdown −15.5846%, terminal value $169.293m |
| Conditional hybrid | The same four other modules, with an added drift on the historical FICC path | CAGR 7.2567%, Sharpe 0.94932, maximum drawdown −14.4262%, terminal value $200.965m |
| FICC 20-year flat-carry scenario | Future cash flows under constant reinvestment rates and no base-case default | CAGR 5.50835%, terminal value $175.343m |

The hybrid's 7.26% CAGR needs particular care. We fit its FICC drift after seeing the full historical sample, so that FICC's terminal growth matches the forward scenario. It is a sensitivity analysis, rather than an actual historical FICC return or a forecast. The other four modules stay unchanged.

The FICC forward case assumes that the credit pool keeps earning about 6.0661% a year, cash earns 3.6823%, and there is no default or downgrade. Reinvestment at lower rates would reduce the result. The 6.04% USD Funding Grid is the borrowing rate, not the return on our bonds. Our six-bond historical test uses a credit ETF proxy because we do not have those bonds' complete daily price histories.

The [methods](docs/METHODS.md) explain the calculations. The [limitations](docs/LIMITATIONS.md) cover the assumptions that matter when interpreting them.

## Reproduce the calculations

The offline run needs no API key or Bloomberg terminal. We used Python 3.12.14, NumPy 2.3.5 and pandas 2.2.3 for the saved run. The package is intended for Python 3.11–3.14.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/reproduce.py --output results/local
```

This checks the file hashes, rebuilds the equity, commodity and crypto note calculations, replays FICC accounting and the FX model returns, and recalculates daily and weekly portfolio metrics. It compares the outputs with `checks/expected_metrics.json`.

The output folder contains `metrics.json`, reconstructed note NAVs, issue and rollover records, and the combined historical and hybrid NAVs. `results/accepted/` contains our saved run for comparison. It is the same calculation, not a separate test sample.

If you want to work on the constrained commodity weights, also install `requirements-research.txt`. To rebuild the inputs from their original sources, start with [data acquisition](docs/DATA_ACQUISITION.md).

## ESG review

Our [ESG research notes](research/esg_20261011/README.md) record dated public evidence for the six credit issuer groups and the checks we would require before adding exposure or renewing a contract. We keep this review separate from the historical backtest. It has not changed the historical NAVs, and source coverage alone does not mean an issuer has passed the full review.

## What is included

The included inputs reproduce our published model calculation. A full reconstruction from original security records would also need the missing historical stock universe, raw provider files, dealer prices, implied-volatility data and final issuer terms. Those gaps remain open.

We publish derived research inputs and source references, rather than raw third-party downloads or private team spreadsheets. Provider data can change, and a fresh download may differ from the version we used. `docs/source_provenance.json` and `checks/sha256_manifest.json` record file identities and hashes.

This is a competition research repository. It does not place trades or contain signed issuer quotes. Natixis has not endorsed the proposal. Publishing these files does not grant a general reuse license for our code or for the underlying providers' data, reports and prospectuses.
