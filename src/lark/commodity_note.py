from __future__ import annotations
import json, math, statistics
from bisect import bisect_right
from datetime import date
from typing import Any
START=date(2016,9,30); CUTOFF=date(2026,9,17)
INITIAL_CAPITAL=5_000_000.; ISSUE_FEE=.005; VOL_LOOKBACK=252
COMMODITY_TERM_Y=5; CRYPTO_TERM_Y=3; COMMODITY_BUFFER=.25
CRYPTO_LEGACY_CAP=.80; CRYPTO_UNDERLYING_FEE=.0025
BASE_WEIGHTS={'Gold':.50,'Copper':.15,'Silver':.15,'WTI':.20}
GOLD40_WEIGHTS={'Gold':.40,'Copper':.183333333333,'Silver':.183333333333,'WTI':.233333333334}


def last_known_curve(curves: dict[date, dict[float, float]], d: date) -> dict[float, float]:
    ks = [x for x in curves if x <= d]
    if not ks:
        raise ValueError(f"No Treasury curve available on or before {d}")
    return curves[ks[-1]]


def interp(x: float, xs: list[float], ys: list[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            w = (x - xs[i-1]) / (xs[i] - xs[i-1])
            return ys[i-1] * (1 - w) + ys[i] * w
    return ys[-1]


def treasury_df(curve: dict[float, float], T: float) -> float:
    """Bootstrap a simple semiannual par curve to discount factors.

    Treasury par yields are official daily observations. This is an approximate
    coupon-bond bootstrap with semiannual coupons; it is not an OIS/issuer curve.
    """
    if T <= 0:
        return 1.0
    par_x = sorted(curve)
    par_y = [curve[x] for x in par_x]
    def par_rate(t: float) -> float:
        return interp(t, par_x, par_y)
    dfs: dict[float, float] = {0.0: 1.0}
    short = max(-0.05, par_rate(0.25))
    dfs[0.25] = math.exp(-short * 0.25)
    for n in range(1, 61):
        t = n * 0.5
        c = par_rate(t)
        prior = sum(dfs[k * 0.5] for k in range(1, n))
        df = (1.0 - (c / 2.0) * prior) / (1.0 + c / 2.0)
        if not math.isfinite(df) or df <= 0:
            df = math.exp(-c * t)
        dfs[t] = df
        if t >= min(10.0, max(par_x)):
            break
    if T <= 0.25:
        return math.exp(math.log(dfs[0.25]) * T / 0.25)
    if T <= max(dfs):
        xs = sorted(dfs)
        return math.exp(interp(T, xs, [math.log(dfs[x]) for x in xs]))
    y = par_rate(min(T, max(par_x)))
    return math.exp(-y * T)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call_put(S: float, K: float, T: float, df: float, sigma: float, q: float = 0.0) -> tuple[float, float, float, float]:
    if T <= 1e-10:
        return max(S-K, 0.0), max(K-S, 0.0), (1.0 if S > K else 0.0), (-1.0 if S < K else 0.0)
    sigma = max(0.01, sigma)
    r = -math.log(max(df, 1e-12)) / T
    root = sigma * math.sqrt(T)
    d1 = (math.log(max(S, 1e-12) / K) + (r - q + 0.5*sigma*sigma) * T) / root
    d2 = d1 - root
    eq = math.exp(-q*T)
    call = S*eq*norm_cdf(d1) - K*df*norm_cdf(d2)
    put = K*df*norm_cdf(-d2) - S*eq*norm_cdf(-d1)
    return max(call, 0.0), max(put, 0.0), eq*norm_cdf(d1), eq*(norm_cdf(d1)-1.0)


def trailing_sigma(index: dict[date, float], dates: list[date], i: int, lookback: int = VOL_LOOKBACK, annualization: int = 252) -> float:
    # Current date is excluded: all vol inputs are causal.
    lo = max(1, i - lookback)
    rets = []
    for j in range(lo, i):
        p0, p1 = index[dates[j-1]], index[dates[j]]
        if p0 > 0 and p1 > 0:
            rets.append(math.log(p1 / p0))
    if len(rets) < 30:
        # Warmup data normally supplies a full lookback; this is an explicit fallback.
        return 0.30
    return max(0.05, statistics.stdev(rets) * math.sqrt(annualization))


def next_market_date(dates: list[date], target: date) -> date | None:
    for d in dates:
        if d >= target:
            return d
    return None


def add_years(d: date, n: int) -> date:
    try:
        return d.replace(year=d.year+n)
    except ValueError:
        return d.replace(year=d.year+n, day=28)


def commodity_payoff_multiple(R: float, alpha: float) -> float:
    if R >= 0:
        return 1.0 + alpha*R
    if R >= -COMMODITY_BUFFER:
        return 1.0
    return max(COMMODITY_BUFFER, 1.0 + R + COMMODITY_BUFFER)


def crypto_payoff_multiple(R: float, alpha: float, cap: float) -> float:
    return 1.0 + alpha*min(max(R, 0.0), cap)


def option_components(kind: str, S: float, T: float, curve: dict[float,float], sigma: float, alpha: float, cap: float = CRYPTO_LEGACY_CAP) -> dict[str,float]:
    df = treasury_df(curve, T)
    if kind == "commodity":
        c, _, cd, _ = bs_call_put(S, 1.0, T, df, sigma, q=0.0)
        _, p, _, pd = bs_call_put(S, 0.75, T, df, sigma, q=0.0)
        debt = df
        opt = alpha*c - p
        delta = alpha*cd - pd
        return {"df": df, "debt": debt, "call": alpha*c, "put_short": -p, "option": opt, "price": debt+opt, "delta": delta, "call_unit": c, "put_unit": p}
    c1, _, d1, _ = bs_call_put(S, 1.0, T, df, sigma, q=CRYPTO_UNDERLYING_FEE)
    c2, _, d2, _ = bs_call_put(S, 1.0+cap, T, df, sigma, q=CRYPTO_UNDERLYING_FEE)
    spread = c1-c2
    opt = alpha*spread
    delta = alpha*(d1-d2)
    return {"df": df, "debt": df, "call": alpha*c1, "short_call": -alpha*c2, "option": opt, "price": df+opt, "delta": delta, "spread_unit": spread}


def issue_alpha(kind: str, S: float, T: float, curve: dict[float,float], sigma: float, fee: float, cap: float = CRYPTO_LEGACY_CAP) -> tuple[float,dict[str,float]]:
    comp0 = option_components(kind, S, T, curve, sigma, 0.0, cap)
    if kind == "commodity":
        c_unit = comp0["call_unit"]
        put_unit = comp0["put_unit"]
        alpha = (1.0 - fee - comp0["df"] + put_unit) / max(c_unit, 1e-12)
    else:
        spread = comp0["spread_unit"]
        alpha = (1.0 - fee - comp0["df"]) / max(spread, 1e-12)
    alpha = max(0.0, alpha)
    return alpha, comp0


def note_spec(name: str, kind: str, alpha_mode: str, fixed_alpha: float | None, cap: float, weights_key: str | None, rebal_key: str | None = None) -> dict[str,Any]:
    return {"name":name,"kind":kind,"alpha_mode":alpha_mode,"fixed_alpha":fixed_alpha,"cap":cap,"weights_key":weights_key,"rebal_key":rebal_key}


def simulate_note(spec: dict[str,Any], dates: list[date], index: dict[date,float], curves: dict[date,dict[float,float]], issue_fee: float = ISSUE_FEE, market_turnover_costs: dict[date,float] | None = None) -> tuple[list[dict[str,Any]],list[dict[str,Any]],list[dict[str,Any]]]:
    start_i = next_market_date(dates, START)
    if start_i is None:
        raise ValueError("no strategy start date")
    kind=spec["kind"]
    tenor=COMMODITY_TERM_Y if kind=="commodity" else CRYPTO_TERM_Y
    sim=[]
    contracts=[]
    cf=[]
    initial=INITIAL_CAPITAL
    wealth=initial
    issue_date=start_i
    maturity=next_market_date(dates, add_years(issue_date,tenor))
    if maturity is None:
        maturity=add_years(issue_date,tenor)
    face=0.0; cash=0.0; alpha=0.0; issue_index=index[start_i]
    issue_info={}
    prior_date=None
    mark_day=0
    for i,d in enumerate(dates):
        if d < start_i:
            continue
        if d > CUTOFF:
            break
        # accrue cash first over the elapsed calendar days using last-known short Treasury yield.
        if prior_date is not None and cash:
            dt=(d-prior_date).days
            rshort=last_known_curve(curves,d).get(0.25,0.0)
            cash *= math.exp(rshort*dt/365.25)
        curve=last_known_curve(curves,d)
        sigma=trailing_sigma(index,dates,i,VOL_LOOKBACK,252)
        S=index[d]/issue_index if issue_index else 1.0
        T=max(0.0,(maturity-d).days/365.25)
        event=""
        redemption=0.0
        reinvested=0.0
        issue_cost=0.0
        pre_issue_nav=None
        # If a note matured since last available market mark, settle and roll today.
        if d >= maturity:
            R=S-1.0
            terminal_mult=commodity_payoff_multiple(R,alpha) if kind=="commodity" else crypto_payoff_multiple(R,alpha,spec["cap"])
            redemption=face*terminal_mult
            wealth_before=redemption+cash
            cf.append({"date":d.isoformat(),"variant":spec["name"],"event":"maturity_redemption","currency":"USD","face_usd":face,"cashflow_usd":redemption,"return_from_issue":R,"payoff_multiple":terminal_mult,"note_alpha":alpha,"remaining_cash_before":cash})
            reinvested=wealth_before
            pre_issue_nav=wealth_before
            wealth=wealth_before
            event="maturity_roll"
            # Start new note in the same product design immediately at the maturity valuation date.
            issue_date=d
            maturity=next_market_date(dates, add_years(issue_date,tenor)) or add_years(issue_date,tenor)
            issue_index=index[d]
            S=1.0
            T=max(0.0,(maturity-d).days/365.25)
            sigma=trailing_sigma(index,dates,i,VOL_LOOKBACK,252)
            if spec["alpha_mode"]=="par_budget":
                alpha,_=issue_alpha(kind,S,T,curve,sigma,issue_fee,spec["cap"])
                at_issue=option_components(kind,S,T,curve,sigma,alpha,spec["cap"])
            else:
                alpha=float(spec["fixed_alpha"])
                at_issue=option_components(kind,S,T,curve,sigma,alpha,spec["cap"])
            price=float(at_issue["price"])
            total_cost=price+issue_fee
            face=wealth/total_cost if total_cost>1.0 else wealth
            cash=max(0.0,wealth-face*total_cost)
            issue_cost=face*issue_fee
            reinvested=face*price+cash
            issue_info={"price":price,"components":at_issue,"sigma":sigma,"curve":curve,"fee":issue_fee,"issue_cost":issue_cost,"issue_date":issue_date,"maturity":maturity}
            contracts.append({"variant":spec["name"],"kind":kind,"issue_date":issue_date.isoformat(),"scheduled_maturity":add_years(issue_date,tenor).isoformat(),"modeled_settlement_date":maturity.isoformat(),"term_years_inferred":tenor,"face_usd":face,"capital_before_issue_usd":wealth,"model_price_per_face":price,"upfront_issue_fee_pct":issue_fee,"issue_fee_usd":issue_cost,"initial_nav_after_fee_usd":face*price+cash,"alpha":alpha,"cap":spec["cap"] if kind=="crypto" else None,"commodity_buffer":COMMODITY_BUFFER if kind=="commodity" else None,"commodity_weights":spec.get("weights_key"),"commodity_target_weights_at_issue":((BASE_WEIGHTS if spec.get("weights_key") in ("fixed50_original","quarterly_rebalanced","monthly_rebalanced") else GOLD40_WEIGHTS) if kind=="commodity" else None),"vol_lookback_days":VOL_LOOKBACK,"issue_rv_ann":sigma,"treasury_par_curve_inputs":curve,"risk_free_bootstrap_discount_factor":at_issue["df"],"issue_components":at_issue,"par_budget_alpha":spec["alpha_mode"]=="par_budget","effective_principal_floor_pct_of_capital":(COMMODITY_BUFFER*face/wealth*100 if kind=="commodity" else 100*face/wealth),"note":"model-mid, conditional on issuer performance; par-curve bootstrap and trailing realized volatility proxy; no firm quote"})
            cf.append({"date":d.isoformat(),"variant":spec["name"],"event":"new_issue","currency":"USD","face_usd":face,"cashflow_usd":-face*price,"fee_usd":issue_cost,"cash_after_issue_usd":cash,"alpha":alpha,"cap":spec["cap"] if kind=="crypto" else None,"term_years":tenor})
        elif d == issue_date and face == 0.0:
            pre_issue_nav=wealth
            event="initial_issue"
            issue_index=index[d]
            if spec["alpha_mode"]=="par_budget":
                alpha,_=issue_alpha(kind,1.0,T,curve,sigma,issue_fee,spec["cap"])
                at_issue=option_components(kind,1.0,T,curve,sigma,alpha,spec["cap"])
            else:
                alpha=float(spec["fixed_alpha"])
                at_issue=option_components(kind,1.0,T,curve,sigma,alpha,spec["cap"])
            price=float(at_issue["price"])
            total_cost=price+issue_fee
            face=wealth/total_cost if total_cost>1.0 else wealth
            cash=max(0.0,wealth-face*total_cost)
            issue_cost=face*issue_fee
            issue_info={"price":price,"components":at_issue,"sigma":sigma,"curve":curve,"fee":issue_fee,"issue_cost":issue_cost,"issue_date":issue_date,"maturity":maturity}
            contracts.append({"variant":spec["name"],"kind":kind,"issue_date":issue_date.isoformat(),"scheduled_maturity":add_years(issue_date,tenor).isoformat(),"modeled_settlement_date":maturity.isoformat(),"term_years_inferred":tenor,"face_usd":face,"capital_before_issue_usd":wealth,"model_price_per_face":price,"upfront_issue_fee_pct":issue_fee,"issue_fee_usd":issue_cost,"initial_nav_after_fee_usd":face*price+cash,"alpha":alpha,"cap":spec["cap"] if kind=="crypto" else None,"commodity_buffer":COMMODITY_BUFFER if kind=="commodity" else None,"commodity_weights":spec.get("weights_key"),"commodity_target_weights_at_issue":((BASE_WEIGHTS if spec.get("weights_key") in ("fixed50_original","quarterly_rebalanced","monthly_rebalanced") else GOLD40_WEIGHTS) if kind=="commodity" else None),"vol_lookback_days":VOL_LOOKBACK,"issue_rv_ann":sigma,"treasury_par_curve_inputs":curve,"risk_free_bootstrap_discount_factor":at_issue["df"],"issue_components":at_issue,"par_budget_alpha":spec["alpha_mode"]=="par_budget","effective_principal_floor_pct_of_capital":(COMMODITY_BUFFER*face/wealth*100 if kind=="commodity" else 100*face/wealth),"note":"model-mid, conditional on issuer performance; par-curve bootstrap and trailing realized volatility proxy; no firm quote"})
            cf.append({"date":d.isoformat(),"variant":spec["name"],"event":"new_issue","currency":"USD","face_usd":face,"cashflow_usd":-face*price,"fee_usd":issue_cost,"cash_after_issue_usd":cash,"alpha":alpha,"cap":spec["cap"] if kind=="crypto" else None,"term_years":tenor})
        # Mark current note. At maturity date already settled and reissued, so current note has nearly full tenor.
        curve=last_known_curve(curves,d)
        S=index[d]/issue_index if issue_index else 1.0
        T=max(0.0,(maturity-d).days/365.25)
        sigma=trailing_sigma(index,dates,i,VOL_LOOKBACK,252)
        comp=option_components(kind,S,T,curve,sigma,alpha,spec["cap"])
        if d == maturity and event != "maturity_roll":
            R=S-1.0
            terminal_mult=commodity_payoff_multiple(R,alpha) if kind=="commodity" else crypto_payoff_multiple(R,alpha,spec["cap"])
            note_mark=face*terminal_mult
        else:
            terminal_mult=None
            note_mark=face*comp["price"]
        nav=note_mark+cash
        rebalance_cost_fraction = float((market_turnover_costs or {}).get(d,0.0))
        if rebalance_cost_fraction>0:
            # Underlying index rebalancing cost is included in the level; record it separately for audit.
            event = (event+"+" if event else "")+"basket_rebalance_cost"
        row={"date":d.isoformat(),"variant":spec["name"],"note_issue_date":issue_date.isoformat(),"nav_usd":nav,"initial_capital_usd":initial,"nav_normalized_to_initial_capital":nav/initial,"nav_pre_issue_usd":pre_issue_nav,"nav_pre_issue_normalized":(pre_issue_nav/initial if pre_issue_nav is not None else None),"note_face_usd":face,"cash_balance_usd":cash,"note_mark_usd":note_mark,"note_price_per_face":comp["price"],"bond_pv_usd":face*comp["debt"],"option_value_usd":face*comp["option"],"option_delta_per_face":comp["delta"],"delta_exposure_usd":face*comp["delta"]*S,"underlying_index":index[d],"underlying_ratio_to_issue":S,"underlying_return_to_issue":S-1.0,"remaining_years":T,"rv_ann_252_prior":sigma,"treasury_3m_cash_rate":curve.get(0.25),"treasury_curve":json.dumps(curve,sort_keys=True),"alpha":alpha,"cap":spec["cap"] if kind=="crypto" else None,"issue_fee_usd":issue_cost,"redemption_cashflow_usd":redemption,"reinvestment_usd":reinvested,"basket_rebalance_cost_fraction":rebalance_cost_fraction,"event":event,"model_terminal_multiple_if_matured_today":(commodity_payoff_multiple(S-1.0,alpha) if kind=="commodity" else crypto_payoff_multiple(S-1.0,alpha,spec["cap"]))}
        sim.append(row)
        # Daily cashflow ledger records valuation components and the actual modeled cash account.
        cf.append({"date":d.isoformat(),"variant":spec["name"],"event":"daily_mark","face_usd":face,"cash_usd":cash,"nav_usd":nav,"note_mark_usd":note_mark,"debt_component_usd":face*comp["debt"],"option_component_usd":face*comp["option"],"underlying_index":index[d],"underlying_return":S-1.0,"sigma_ann":sigma,"remaining_years":T,"rate_inputs":json.dumps(curve,sort_keys=True),"contract_alpha":alpha,"basket_rebalance_cost_fraction":rebalance_cost_fraction})
        prior_date=d
    return sim, contracts, cf

