"""债券策略回测框架、绩效评估与收益归因。

- :func:`nav` / :func:`performance` 由收益序列计算净值与绩效指标；
- :func:`bond_period_return` 把单期债券收益分解为 carry + roll-down + 久期 + 凸性；
- :func:`riding_attribution` 给"骑乘曲线"策略做收益归因。
"""

from __future__ import annotations

import numpy as np


def nav(returns):
    """由单期收益序列计算累计净值。"""
    return np.cumprod(1.0 + np.asarray(returns, dtype=float))


def performance(returns, periods_per_year: int = 252) -> dict:
    """绩效指标：年化收益、年化波动、夏普、最大回撤。"""
    r = np.asarray(returns, dtype=float)
    n = len(r)
    nav_ = nav(r)
    ann_return = float(nav_[-1] ** (periods_per_year / n) - 1.0)
    ann_vol = float(r.std(ddof=1) * np.sqrt(periods_per_year)) if n > 1 else 0.0
    sharpe = float(ann_return / ann_vol) if ann_vol > 0 else float("nan")
    max_dd = float((nav_ / np.maximum.accumulate(nav_) - 1.0).min())
    return {"ann_return": ann_return, "ann_vol": ann_vol, "sharpe": sharpe, "max_drawdown": max_dd}


def bond_period_return(yield_start, yield_end, duration, convexity, coupon_rate, dt: float = 1.0) -> dict:
    """单期债券收益分解（近似）：carry + 久期收益 + 凸性。

    总收益 ≈ 票息收入 + (−久期×Δy + ½凸性×Δy²)。
    """
    dy = yield_end - yield_start
    carry = coupon_rate * dt
    duration_ret = -duration * dy
    convexity_ret = 0.5 * convexity * dy ** 2
    total = carry + duration_ret + convexity_ret
    return {"carry": carry, "duration": duration_ret, "convexity": convexity_ret, "total": total}


def riding_attribution(y_buy, y_sell, duration, coupon_rate, horizon: float = 1.0) -> dict:
    """骑乘曲线（riding the yield curve）策略的收益归因。

    买入较长期限债持有 ``horizon`` 后卖出：曲线不变时债券沿曲线"下滚"到更低收益率，
    带来 roll-down 资本利得。总收益 = carry（票息）+ roll-down（−久期×(y_sell−y_buy)）。
    """
    carry = coupon_rate * horizon
    rolldown = -duration * (y_sell - y_buy)
    return {"carry": carry, "rolldown": rolldown, "total": carry + rolldown}


def run_backtest(returns) -> dict:
    """最小回测：由单期收益序列返回净值与绩效。"""
    return {"nav": nav(returns), "performance": performance(returns)}
