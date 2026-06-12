"""风险价值（VaR）与条件风险价值（CVaR/ES）：历史、参数、蒙特卡洛三法，及压力/情景。

VaR 回答"在置信水平 α 下，给定持有期内最大可能损失是多少"；CVaR（期望损失/ES）回答
"一旦突破 VaR，平均损失多大"。债券组合的损益由久期 × 收益率变动驱动。
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def historical_var(pnl, alpha: float = 0.99) -> float:
    """历史模拟法 VaR：损益经验分布的 (1−α) 分位数（取正损失）。"""
    return float(-np.percentile(np.asarray(pnl, dtype=float), (1 - alpha) * 100))


def historical_cvar(pnl, alpha: float = 0.99) -> float:
    """历史模拟法 CVaR（ES）：超过 VaR 的尾部损失均值。"""
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
    """债券组合损益的标准差 ≈ 久期 × 市值 × 收益率波动率。"""
    return float(duration * value * yield_vol)


def scenario_pnl(value, duration, convexity, dy) -> float:
    """情景分析：给定收益率变动 dy，组合损益 ≈ 市值 ×(−久期·dy + ½凸性·dy²)。"""
    return float(value * (-duration * dy + 0.5 * convexity * dy ** 2))
