# What to keep in mind when reading our results

Our results describe the models and inputs in this repository. The main limits are below, grouped by how they affect the investment case.

## Historical data and selection

Market inputs end on 17 September 2026. We carried out research and published the repository later. A later webpage cannot establish what the strategy knew at the cutoff.

The equity pool still misses some historical exits and does not have complete historical share counts, industries or Asian financial statements. The partial point-in-time records improve the inputs but do not remove all selection bias. We have already seen the shortlist and the backtest periods, so a chronological holdout should not be described as a blind out-of-sample test.

The included note inputs reproduce our calculations. They do not independently rebuild every raw source. Revised provider files may no longer match the captured hashes.

Asian, US and UTC crypto closes occur at different times. Combining their marks gives a useful accounting series, but not a set of prices available for simultaneous execution. ETF histories also reflect vehicle changes, futures roll, expenses and premiums or discounts. Changing a contract from ETF shares to a spot or futures index requires a new test.

## Valuation and contractual protection

We do not have a complete five-year basket implied-volatility surface, issuer credit curve or dealer spread history. Realized volatility and shorter public volatility indices are approximations. Actual option prices could change the participation rate or the budget needed for protection.

Modeled protection is not a signed guarantee. Multiple reference companies or commodities do not diversify the bank issuing a note. Our proposed policy requires at least three independent bank-parent groups, with no group exceeding one-third of funded note face. We have not demonstrated a historical multi-bank issuance programme under those limits. The main NAV calculation excludes issuer default.

The exact securities, issue-date legal access, sanctions clearance, final contract rights and issuer quotes remain to be confirmed. Public security IDs, source URLs and turnover screens do not settle those questions or prove Bloomberg verification. The terms in this repository are model assumptions, rather than executable bank quotes. If options cost more, we must reduce participation, add a cap or allocate more budget. We cannot quietly remove the stated protection.

## FICC, cash and the investment horizon

FICC's historical test uses CEMB and fitted Treasury zero curves because the exact six-bond daily histories are missing. Reinvestment rates and terminal sale prices affect the future cash-flow result.

The $60m Treasury face is a redemption target, not a $60m purchase cost or an automatic guarantee to the noteholder. The plan requires the principal to be retained for the 33 days between the Treasury maturity and the policy horizon. The actual bridge arrangement still needs confirmation. Nominal protection does not preserve purchasing power or prevent losses on an early sale.

VUSXX has a variable yield and its own dealing and settlement arrangements. Cash access also depends on custody and the receiving bank. Smoothing distributions into daily accrual is an accounting approximation. It reduces measured cash volatility and does not prove a same-day payment timetable.

## Interpreting performance

The hybrid adjusts historical FICC growth using the observed terminal value. It is a hindsight sensitivity. The 20-year FICC scenario depends on its reinvestment and default assumptions. Neither calculation guarantees the returns of a future five-year note or a 20-year portfolio.

Extreme maturity scenarios check the payment formula, not the probability of those outcomes. The ES99 estimate uses 26 tail observations and cannot tell us the likelihood of a remote issuer default. We also do not claim that the chosen strategy is the best possible allocation.
