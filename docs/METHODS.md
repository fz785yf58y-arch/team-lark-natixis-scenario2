# How we built and tested the portfolio

## Dates, capital and return measures

Our common test runs from 30 September 2016 to 17 September 2026. It contains 2,504 NAV observations and 2,503 returns, spanning 9.963039 calendar years.

We start with $100m. Initial modeled fees reduce the opening net assets to $99.225m. We measure the first return against the original $100m so that the opening costs remain in the results. In this version, we do not periodically reset the five module weights to their initial allocation. Each module follows its own rules, and its portfolio weight drifts with performance.

We add the dollar NAVs before calculating total-portfolio returns. We merge source dates with the common calendar, then carry the latest known mark forward. This preserves FX observations on dates outside the common calendar. We do not interpolate using future prices. Asian exchanges, US exchanges and crypto still have different closing times, which limits how precisely the combined daily series describes simultaneous market risk.

Our metric definitions are:

- `CAGR = (terminal value / initial capital)^(365.25 / elapsed days) - 1`.
- Annualized volatility is the sample standard deviation of daily returns multiplied by `sqrt(252)`.
- Sharpe is the mean daily excess return divided by its sample standard deviation, multiplied by `sqrt(252)`. We use a 2% effective annual risk-free rate, accrued over each actual calendar-day gap.
- Maximum drawdown includes the original capital as the starting observation.

Weekly metrics use each week's last available mark, plus inception and the final partial week. We do not extend the data beyond the cutoff to create a Friday observation.

## Equities

We begin with the team's quarterly shortlist and market-cap-weighted core. The core accounts for 80% of the basket. Fast Retailing, INDA and GRAB occupy three satellite slots totaling 20%. Before GRAB begins trading, we hold its slot in cash.

Our refinement removes the three weakest names by risk-adjusted momentum when the constraints allow it, then weights the remaining names by inverse volatility. If the caps make that allocation infeasible, we restore names in rank order. If the required features are incomplete, we use the original quarterly target. Target caps are 8% per name, 35% per region and 40% per theme. Weights can drift between quarterly resets.

Momentum averages the six- and twelve-month returns while skipping the latest month. Twelve-month history may be unavailable during warmup. Volatility uses 126 sessions. We stop the feature window two US sessions before the quarterly signal and execute at the next available session close.

For stocks with suitable disclosures, we apply a 25% quality tilt based on profit/assets and operating cash flow/assets. We match consolidated reporting scope, fiscal end, currency and filing accession. A disclosure becomes available to the strategy at least two calendar days after publication. Missing quality data is treated as unknown, rather than a poor score. The tilted weights use the same basket constraints.

Historical market cap is still partly estimated, and the stock pool is partly retrospective. Ranking by market cap does not remove survivorship bias when a delisted or missing company never entered the pool.

We charge 10bp on each gross purchase or sale. Initial funding uses one-sided turnover. Later rebalances use the full L1 change in weights.

The client instrument is modeled as a five-year note referencing the basket. Its maturity payoff is:

```text
payoff / face = 0.90 + alpha * min(max(underlying return, 0), 1)
```

The 90% floor applies at maturity and depends on the issuing bank paying. It is not a floor under daily NAV. At each issue, we solve participation `alpha` from the budget using a 50bp issue fee, fitted Treasury discounting and lagged 126-session realized volatility, clipped to 10–60%. Participation stays fixed for that contract. At maturity, the proceeds fund a new note with newly calculated terms.

## Commodities

Our proposed note references ETF share prices: GLD, CPER, SLV and USO. It is not a commodity spot index. Starting weights are 50%, 15%, 15% and 20%, respectively.

Each quarter, we estimate covariance from 252 sessions of log returns and shrink it 50% toward its diagonal. We solve for constrained minimum-variance weights, then blend those weights equally with the starting allocation. Bounds are 35–65% for gold and 10–25% each for copper, silver and WTI. The adopted signal has an extra day's lag. Basket trades cost 10bp on full L1 turnover.

The five-year note has a 25% maturity buffer:

```text
payoff / face = 1 + alpha * max(R, 0) - max(-R - 0.25, 0)
```

Here `R` is the basket's return over the contract, with `R >= -1`. If the basket ends down 30%, 50% or 80%, the note loses 5%, 25% or 55% of face. These examples show how the payoff works. They do not estimate the likelihood of a loss.

We solve participation at every issue using Treasury discounting, a long at-the-money call, a short put struck at 75% of the initial basket level and a 50bp issue fee. We cannot simply choose 120% participation without paying for it.

Daily NAV values the debt and option legs using remaining maturity and the lagged realized-volatility proxy. NAV can therefore fall below 75% before maturity even though the final payoff has a 25% buffer. ETF prices already reflect vehicle expenses and futures roll effects, so we do not deduct those effects again.

## Crypto

We retain the team's three-year principal-protected call-spread structure:

```text
payoff / face = 1 + alpha * min(max(R, 0), 1)
```

Participation comes from the issue budget, using Treasury discounting, a 50bp issue fee, lagged realized volatility and a cap at a 100% underlying return. The earlier team case with fixed participation and an 80% cap, and the book that kept notes at cost, use different conventions. They are not the main NAV series in this version.

Before IBIT existed, we use BTC with a fee proxy. From January 2024, we use IBIT share prices. This gives us a longer test, but it is a mixed history rather than ten years of actual IBIT returns.

Every three-year maturity settles before a new note is issued. Between maturities, NAV follows the option valuation model, rather than original cost or the principal floor. The main series excludes issuer default.

## FX/Rate

KR4 works with estimated factor returns. Each month, a ten-year mean/covariance estimate sets a coefficient book targeting roughly 10% annual factor volatility.

Half the book uses a 63-day signed trend with EWMA risk scaling. The other half uses a soft trend that averages standardized cumulative returns over 63, 126 and 252 days, with 63-day volatility scaling. Scaling reduces exposure when risk rises and stays within its cap. The return calculation applies decisions after a two-available-close lag.

We include modeled cash carry and deduct an assumed 1% annual NAV drag. The coefficients describe factor exposure, rather than executable positions in named futures or swaps.

The original estimated-factor archive ends on 27 June 2025. Later observations use our Treasury-PCA architecture proxy. Source-regime flags identify that change. Dollar attribution uses the previous native NAV multiplied by the cash, factor and cost return components, and reconciles to final NAV less the original $5m.

## FICC

The current 20-year budget is:

| Component | Initial amount |
|---|---:|
| Treasury modeled purchase cost | $20.488211m |
| Credit pool, including the legacy growth amount | $34.931080m |
| Staged put premium | $0.980709m |
| Cash | $3m |
| Initial fee | $0.6m |

The legacy growth amount goes into the credit pool. It is not a separate growth option obtained for free. The annual fee is $0.12m.

Credit weights are TSMC 1/9, Tencent 1/9, LG Energy Solution 1/6, Meituan 1/6, Alibaba 2/9 and Reliance 2/9. The clean prices plus accrued interest used in the model give a weighted effective annual yield of 6.0661%.

In our flat-carry forward scenario, the credit pool compounds at that yield for 20 years, cash earns 3.6823%, and the Treasury component returns $60m of principal. We deduct the future value of 20 annual fees at the blended asset hurdle. The puts expire worthless in this base case. The result is $175.343m, equivalent to a 5.50835% CAGR. Keeping that reinvestment rate for 20 years is an assumption, not a yield we have locked for every future cash flow.

The protection consists of modeled European puts expiring after 5, 10 and 15 years on a fixed-maturity Treasury zero-price proxy. Each strike equals 80% of the inception forward price for that expiry. We use Black76, fitted Treasury discounting and lagged five-year realized volatility. The premium budget purchases only partial notional protection. We do not buy a 20-year put because the zero redeems at par at its own maturity.

For historical risk testing, the STRIP leg uses a Federal Reserve Svensson-curve proxy and the credit leg uses CEMB total returns. We do not have a complete transaction-price history for the exact CUSIP or the six credit bonds. VUSXX distributions are accrued smoothly across days. That treatment reduces observed cash volatility and does not demonstrate same-day receipt of cash.

## The conditional hybrid

The hybrid keeps the historical FICC path but adds a constant drift to bring its terminal growth to the forward-case CAGR. Let `Y = 9.963039` years, `F_T` be the historical FICC terminal NAV, and `g = 5.50835%`:

```text
D = [60m * (1 + g)^Y / F_T]^(1 / Y)
F_hybrid(t) = F_historical(t) * D^elapsed_years(t)
```

This uses the final historical observation to choose `D`. We therefore report it as a hindsight sensitivity, not an independent backtest, an actual past return or a forecast. The other four modules are unchanged.
