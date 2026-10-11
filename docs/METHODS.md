# Backtest and allocation methods

## Portfolio metrics and clocks

The common window is 30 September 2016–17 September 2026: 2,504 marks,
2,503 returns, 9.963039 calendar years. Capital is $100m; opening net assets
are $99.225m after initial modeled fees. The first holding-period return is
measured from initial capital, not opening post-fee assets. No module-level
strategic rebalance is inserted in this frozen portfolio; module weights drift.

Dollar NAVs are added before portfolio returns are computed. Source dates are
unioned with the common calendar **before** last-known-mark forward carry;
native FX updates on non-common dates are preserved. No future-price linear
interpolation is used. Asian, US and crypto closing clocks differ.

`CAGR=(terminal/capital)^(365.25/elapsed_days)-1`.
Annualized volatility uses sample daily return standard deviation times
sqrt(252). Sharpe uses the mean and sample standard deviation of daily excess
returns times sqrt(252), with a 2% effective annual risk-free rate applied over
each actual calendar-day gap. Maximum drawdown includes the initial capital
anchor. Weekly results take the last observed mark per week plus inception and
the partial final week; they do not invent a post-cutoff Friday.

## Equities

The teammate's quarterly shortlist and market-cap-weighted core remain the
starting point. The 80% core is complemented by three satellite slots totalling
20%: Fast Retailing, INDA and GRAB; the GRAB slot is cash before its trading
start. The adopted refinement removes the three weakest risk-adjusted momentum
names when caps permit, then inverse-volatility weights the remainder. If caps
are infeasible, names are restored in rank order; if complete features are
missing, the original quarter target is used. Name/region/theme target caps are
8%/35%/40%. Targets may drift between quarter resets.

Momentum averages 6- and 12-month returns while skipping the most recent month;
12-month history can be absent in warmup. Volatility uses 126 sessions. Features
end two US sessions before the quarter signal, with execution at the next
available session close. Market-cap history remains partly proxied and the
pool partly retrospective. Being ranked by market cap does not eliminate
survivorship bias if missing/retired stocks never entered the pool.

For covered stocks, the adopted 25% quality tilt ranks profit/assets and
operating cash flow/assets. Each ratio uses matching consolidated disclosure,
fiscal end, currency and accession. Publication must precede feature availability
by at least two calendar days. Unknown quality is not treated as low quality.
The tilt is capped/projected with the same original basket constraints.

Every gross purchase or sale costs 10bp; initial funding is one-sided, later
transactions use the full L1 weight turnover. The investor is modeled as holding
a 5Y note, not every reference stock. Its payoff per face is
`0.90 + alpha*min(max(underlying_return,0),1)`.
The 90% maturity floor is conditional on the bank paying, not a daily NAV floor.
Each issue solves alpha from a 50bp issue fee, fitted Treasury discount and
lagged 126-session realized-volatility proxy clipped to 10–60%. Alpha stays
fixed during the contract. Maturity proceeds roll to a newly budgeted note.

## Commodities

Contract research is linked to ETF share prices: GLD, CPER, SLV and USO, not
interchangeably to commodity spot. Base weights are 50/15/15/20%. Each quarter
uses 252-session covariance of log returns, shrinks 50% toward its diagonal,
solves constrained minimum variance, then blends 50% with base weights.
Bounds are Gold35–65%, Copper10–25%, Silver10–25%, WTI10–25%. The adopted
signal has an extra day's lag. Basket transactions cost 10bp full L1 turnover.

The note has 5Y maturity and a 25% maturity buffer:
`payoff/face = 1 + alpha*max(R,0) - max(-R-0.25,0)` for economically valid
underlying returns R >= −1. At −30/−50/−80% underlying return the note loses
5/25/55% of face; these are payoff identities, not loss probabilities.
Alpha is budget-solved each issue with a 50bp fee, a long ATM call and short
75%-strike put plus Treasury discount. It is not freely set to 120%.
Daily NAV marks debt plus options using the causal RV proxy and remaining
tenor, so it can fall below 75% before maturity. Embedded ETF expenses and
futures roll effects are not deducted a second time.

## Crypto

The adopted note keeps the teammate's 3Y principal-protected call-spread
direction: `payoff/face = 1 + alpha*min(max(R,0),1)`.
Alpha is solved from the issue budget using the Treasury discount, 50bp fee,
lagged RV and 100%-underlying-return cap. The earlier fixed-alpha80%-cap team
case and cost-flat book are different research conventions, not the adopted
main path. BTC with a fee proxy precedes IBIT inception; IBIT share prices are
used from January 2024. That hybrid underlying is an explicit history proxy.
Every 3Y maturity settles then issues new terms. Interim NAV is option-model
value rather than original cost or principal floor; issuer default is excluded.

## FX / Rates

KR4 uses estimated factor return series. A monthly 10Y mean/covariance book
targets approximately10% annual factor volatility. Half the coefficient book
uses 63-day signed trend plus EWMA risk scaling; half uses a soft trend averaging
63/126/252-day standardized cumulative returns and 63-day volatility scaling.
Risk scaling cuts exposure; it does not automatically lever up beyond its cap.
Earned factor coefficients lag decisions by two available closes. Modeled cash
carry is included, and an assumed1% annual NAV drag is applied. Coefficients are
not executable futures or swap holdings.

The author estimated-factor archive stops27 June2025; later history uses the
retained Treasury-PCA architecture proxy. Frozen returns and source-regime
flags disclose this change. Dollar attribution sums prior native NAV times
cash/factor/cost return components, which closes to final NAV less initial$5m.

## FICC and the hybrid

The six-pocket current 20Y forward budget is: Treasury model cost$20.488211m;
direct-credit plus legacy growth pool$34.931080m; staged put premium$0.980709m;
cash$3m; initial fee$0.6m. The legacy growth amount is reinvested into credit,
not a separate free growth option. Annual fee is$0.12m.

Credit weights are TSMC1/9, Tencent1/9, LG Energy1/6, Meituan1/6,
Alibaba2/9, Reliance2/9. Current clean plus accrued prices yield weighted
EAY6.0661%. The illustrative forward case compounds that pool at this rate
for20years, cash at3.6823%, adds$60m principal redemption and deducts the
future value of20annual fees at the blended asset hurdle. Puts expire worthless
in its flat base case. Result:$175.343m, CAGR5.50835%.

Protection consists of modeled European puts expiring in5/10/15years on a
fixed maturity Treasury zero-price proxy; each strike is80% of that expiry's
inception forward price. Black76 valuation uses fitted Treasury discount and
causal5Y realized vol. The premium funds partial, not full, notional. No20Y
put is purchased because the zero pays par at its own maturity. The historical
STRIP component is a Federal Reserve Svensson-curve proxy, not exact CUSIP
transaction history; the credit component is a CEMB total-return proxy.
VUSXX published distributions are smoothed into daily accrual, compressing
observed cash volatility and not establishing same-day payment receipt.

For the displayed hybrid, let Y be the observed9.963039years, F_T the frozen
FICC terminal NAV and g the forward5.50835% rate. The drift is
`D=[60m*(1+g)^Y/F_T]^(1/Y)` and each FICC mark becomes
`F_hybrid(t)=F_historical(t)*D^elapsed_years(t)`.
This condition uses the terminal historical observation. It is a hindsight
sensitivity, not a past achievement, independent forecast or new backtest.
