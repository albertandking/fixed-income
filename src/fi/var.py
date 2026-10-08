"""风险价值（VaR）与条件风险价值（CVaR/ES）：经验分位数、参数与蒙特卡洛方法，及情景损益。

VaR 是给定持有期与损益模型下的损失分位数；ES 描述最差一部分结果的平均损失。
本模块的债券损益函数（:func:`bond_pnl_sigma`、:func:`scenario_pnl`）采用单一收益率因子的
久期（—凸性）近似。
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def historical_var(pnl, alpha: float = 0.99) -> float:
    """输入损益的经验分位数；仅当输入为历史损益时才是历史模拟法。"""
    return float(-np.percentile(np.asarray(pnl, dtype=float), (1 - alpha) * 100))


def historical_cvar(pnl, alpha: float = 0.99) -> float:
    """输入损益中达到或超过经验 VaR 门槛的平均损失。"""
    pnl = np.asarray(pnl, dtype=float)
    var = historical_var(pnl, alpha)
    tail = pnl[pnl <= -var]
    return float(-tail.mean()) if tail.size else var


def parametric_var(sigma, alpha: float = 0.99, mean: float = 0.0) -> float:
    """参数法（正态）VaR：:math:`z_\\alpha\\sigma-\\mu`。"""
    return float(norm.ppf(alpha) * sigma - mean)


def parametric_cvar(sigma, alpha: float = 0.99, mean: float = 0.0) -> float:
    """参数法（正态）CVaR：:math:`\\sigma\\,\\phi(z_\\alpha)/(1-\\alpha)-\\mu`。"""
    z = norm.ppf(alpha)
    return float(sigma * norm.pdf(z) / (1 - alpha) - mean)


def monte_carlo_var(sigma, alpha: float = 0.99, mean: float = 0.0, n: int = 200000, seed: int = 0):
    """蒙特卡洛法 VaR/CVaR（正态情景）。返回 ``(var, cvar)``。"""
    rng = np.random.default_rng(seed)
    sims = rng.normal(mean, sigma, n)
    var = float(-np.percentile(sims, (1 - alpha) * 100))
    cvar = float(-sims[sims <= -var].mean())
    return var, cvar


def bond_pnl_sigma(value, duration, yield_vol) -> float:
    """单一利率因子下的损益标准差近似：久期 × 市值 × 收益率变动标准差。"""
    return float(duration * value * yield_vol)


def scenario_pnl(value, duration, convexity, dy) -> float:
    """情景分析：给定收益率变动 dy，组合损益 ≈ 市值 ×(−久期·dy + ½凸性·dy²)。"""
    return float(value * (-duration * dy + 0.5 * convexity * dy ** 2))
