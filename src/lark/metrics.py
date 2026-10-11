from __future__ import annotations
import math
import numpy as np
import pandas as pd

def weekly_marks(s):
    # Last observed mark of each ISO week, plus inception and the final partial
    # week. No synthetic Friday after the cutoff.
    weekly = s.groupby(s.index.to_period("W-FRI")).tail(1)
    return pd.concat([s.iloc[:1], weekly]).loc[lambda x: ~x.index.duplicated()].sort_index()


def stats(s, capital=None, frequency=252, rf_index=None):
    s = s.astype(float)
    if len(s) < 3:
        return {"marks": len(s), "available": False}
    values = s.to_numpy()
    anchor = float(values[0] if capital is None else capital)
    elapsed = (s.index[-1] - s.index[0]).days / 365.25
    # For whole-window capital returns, charge the initial cost in the first
    # holding-period return. Net opening assets are disclosed separately.
    previous = values[:-1].copy()
    previous[0] = anchor
    returns = values[1:] / previous - 1
    days = np.diff(s.index.to_numpy()).astype("timedelta64[D]").astype(float)
    rf = np.expm1(np.log1p(.02) * days / 365.25)
    if rf_index is not None:
        cash = rf_index.reindex(s.index).to_numpy()
        rf = cash[1:] / cash[:-1] - 1
    excess = returns - rf
    vol = returns.std(ddof=1) * np.sqrt(frequency)
    ex_sd = excess.std(ddof=1)
    running_peak = np.maximum.accumulate(np.r_[anchor, values])[1:]
    dd = values / running_peak - 1
    worst = int(np.argmin(dd))
    peak_pos = int(np.argmax(values[:worst + 1]))
    tail95 = np.sort(returns)[:max(1, int(math.ceil(len(returns) * .05)))]
    tail99 = np.sort(returns)[:max(1, int(math.ceil(len(returns) * .01)))]
    return {"start": str(s.index[0].date()), "end": str(s.index[-1].date()), "years": elapsed,
            "marks": len(s), "returns": len(returns), "opening_net_nav": float(values[0]),
            "invested_capital_or_window_anchor": anchor, "terminal_nav": float(values[-1]),
            "total_return": float(values[-1] / anchor - 1),
            "cagr": float((values[-1] / anchor) ** (1 / elapsed) - 1),
            "annualized_vol": float(vol),
            "sharpe": float(excess.mean() / ex_sd * np.sqrt(frequency)) if ex_sd > 1e-14 else None,
            "max_drawdown": float(dd[worst]), "drawdown_peak_date": str(s.index[peak_pos].date()),
            "drawdown_trough_date": str(s.index[worst].date()),
            "worst_period_return": float(returns.min()), "best_period_return": float(returns.max()),
            "expected_shortfall_95_loss": float(-tail95.mean()),
            "expected_shortfall_99_loss": float(-tail99.mean()), "es99_tail_observations": len(tail99),
            "risk_free": "VUSXX smoothed distribution proxy" if rf_index is not None else "2% effective annual with actual calendar-day gaps",
            "annualization_periods": frequency}

