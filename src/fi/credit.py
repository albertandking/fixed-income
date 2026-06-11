"""信用风险：结构化模型（Merton/KMV）与约化模型（强度模型）。

- **结构化模型**：把股权看作公司资产对负债的看涨期权，由资产价值/波动率推出违约距离与违约概率；
- **约化模型**：把违约视为强度（hazard rate）驱动的随机事件，由信用利差反推违约强度与生存概率；
- 二者都能把"信用利差"翻译成"违约概率"。
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


# ---------------------------------------------------------------------------
# 结构化模型（Merton）
# ---------------------------------------------------------------------------

def merton_pd(asset_value, debt, asset_vol, r, t) -> dict:
    """Merton 模型：违约距离与（风险中性）违约概率。

    :math:`d_2=\\dfrac{\\ln(V/D)+(r-\\tfrac12\\sigma_V^2)t}{\\sigma_V\\sqrt t}`，
    违约距离 = d_2，违约概率 :math:`PD=N(-d_2)`。
    """
    V, D, sig = asset_value, debt, asset_vol
    d2 = (np.log(V / D) + (r - 0.5 * sig ** 2) * t) / (sig * np.sqrt(t))
    return {"distance_to_default": float(d2), "pd": float(norm.cdf(-d2))}


def merton_credit_spread(asset_value, debt, asset_vol, r, t) -> float:
    """Merton 模型隐含的信用利差（连续复利）。

    风险负债现值 :math:`B=V\\,N(-d_1)+D e^{-rt}N(d_2)`，利差 :math:`s=-\\ln(B/D)/t-r`。
    """
    V, D, sig = asset_value, debt, asset_vol
    d1 = (np.log(V / D) + (r + 0.5 * sig ** 2) * t) / (sig * np.sqrt(t))
    d2 = d1 - sig * np.sqrt(t)
    B = V * norm.cdf(-d1) + D * np.exp(-r * t) * norm.cdf(d2)
    return float(-np.log(B / D) / t - r)


# ---------------------------------------------------------------------------
# 约化模型（强度 / hazard rate）
# ---------------------------------------------------------------------------

def hazard_from_spread(spread, recovery: float = 0.4) -> float:
    """由信用利差反推违约强度：:math:`\\lambda\\approx s/(1-R)`（R 为回收率）。"""
    return spread / (1.0 - recovery)


def survival_probability(hazard, t) -> float:
    """常数强度下的生存概率 :math:`S(t)=e^{-\\lambda t}`。"""
    return float(np.exp(-hazard * t))


def default_probability(hazard, t) -> float:
    """常数强度下到 t 的累计违约概率 :math:`1-e^{-\\lambda t}`。"""
    return float(1.0 - np.exp(-hazard * t))


def implied_default_curve(tenors, spreads, recovery: float = 0.4):
    """由各期限信用利差反推累计违约概率曲线（常数回收率近似）。

    Returns
    -------
    (tenors, cumulative_pd) : tuple[numpy.ndarray, numpy.ndarray]
    """
    tenors = np.asarray(tenors, dtype=float)
    spreads = np.asarray(spreads, dtype=float)
    hz = spreads / (1.0 - recovery)
    cum_pd = 1.0 - np.exp(-hz * tenors)
    return tenors, cum_pd
