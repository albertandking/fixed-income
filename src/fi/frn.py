"""浮动利率债券（FRN）定价与利差指标。

浮息债每期票息在重定价日重置为"基准利率 + 票面利差（quoted margin, QM）"。
本模块提供两套定价：

- :func:`price_frn` 教科书"基准利率恒定"模型——直观展示 DM=QM 时价格=面值；
- :func:`price_frn_curve` 用逐期投影的基准（远期）曲线定价，更贴近实务。

并提供由价格反求**折现利差（discount margin, DM）**的求解器。
"""

from __future__ import annotations

import numpy as np


def price_frn(reference, quoted_margin, disc_margin, n_periods, freq: int = 4, face: float = 100.0) -> float:
    """重定价日 FRN 定价（基准利率恒定假设）。

    Parameters
    ----------
    reference : float
        年化基准利率（如 SHIBOR、LPR、DR）。
    quoted_margin : float
        票面利差 QM（写在条款里的固定加点）。
    disc_margin : float
        折现利差 DM（市场对该券要求的利差）。
    n_periods : int
        剩余付息期数。
    freq, face : int, float
        每年付息次数、面值。

    Returns
    -------
    float
        FRN 全价。DM=QM 时恰好等于面值。
    """
    i = (reference + disc_margin) / freq          # 每期折现率
    coupon = (reference + quoted_margin) / freq * face
    ann = (1 - (1 + i) ** (-n_periods)) / i
    return coupon * ann + face * (1 + i) ** (-n_periods)


def price_frn_curve(forwards, quoted_margin, disc_margin, freq: int = 4, face: float = 100.0) -> float:
    """用逐期基准（远期）曲线给 FRN 定价。

    ``forwards[j]`` 为第 ``j`` 期适用的年化基准利率（来自远期曲线）。
    每期票息 = (forwards[j] + QM)/freq·face，折现率 = (forwards[j] + DM)/freq。
    """
    forwards = np.asarray(forwards, dtype=float)
    df = 1.0
    price = 0.0
    for f in forwards:
        df /= 1.0 + (f + disc_margin) / freq
        price += (f + quoted_margin) / freq * face * df
    price += face * df
    return float(price)


def discount_margin(price, reference, quoted_margin, n_periods, freq: int = 4, face: float = 100.0) -> float:
    """由 FRN 价格反求折现利差 DM（基准利率恒定假设）。"""
    from scipy.optimize import brentq

    def f(dm):
        return price_frn(reference, quoted_margin, dm, n_periods, freq, face) - price

    return float(brentq(f, -0.5, 0.5, xtol=1e-12))
