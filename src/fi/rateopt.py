"""利率期权：Cap/Floor 与 Swaption 的 Black 模型定价与隐含波动率。

- **利率上限（Cap）** = 一串 caplet（对每期浮动利率的看涨期权）之和；**下限（Floor）** = 一串 floorlet（看跌）；
- **互换期权（Swaption）** = 进入一笔互换的期权（payer/receiver）；
- 均用 **Black（1976）模型**对"远期利率/远期互换利率"定价。

Cap−Floor 平价：相同执行价下 ``Cap(K) − Floor(K)`` = 一笔付固定 K 的 payer 互换价值。
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def _black(forward, strike, vol, t, call: bool) -> float:
    """Black 公式的"远期"部分（未乘贴现与年金/期限因子）。"""
    d1 = (np.log(forward / strike) + 0.5 * vol ** 2 * t) / (vol * np.sqrt(t))
    d2 = d1 - vol * np.sqrt(t)
    if call:
        return forward * norm.cdf(d1) - strike * norm.cdf(d2)
    return strike * norm.cdf(-d2) - forward * norm.cdf(-d1)


def black_caplet(forward, strike, vol, t, tau, df, notional: float = 1e8, kind: str = "cap") -> float:
    """单个 caplet（kind='cap'）或 floorlet（kind='floor'）的 Black 价值。"""
    return notional * tau * df * _black(forward, strike, vol, t, call=(kind == "cap"))


def black_cap(forwards, strike, vol, times, taus, dfs, notional: float = 1e8, kind: str = "cap") -> float:
    """利率上限（Cap）或下限（Floor）= 各期 caplet/floorlet 之和。"""
    return float(sum(
        black_caplet(f, strike, vol, t, tau, df, notional, kind)
        for f, t, tau, df in zip(forwards, times, taus, dfs)
    ))


def black_swaption(forward_swap_rate, strike, vol, expiry, swap_annuity,
                   notional: float = 1e8, kind: str = "payer") -> float:
    """互换期权（Swaption）的 Black 价值。

    ``swap_annuity`` 为标的互换的年金因子 :math:`\\sum_i\\tau_i DF_i`。
    """
    return float(notional * swap_annuity * _black(
        forward_swap_rate, strike, vol, expiry, call=(kind == "payer")))


def implied_vol(price, forward, strike, t, tau, df, notional: float = 1e8, kind: str = "cap") -> float:
    """由 caplet/floorlet 价格反求 Black 隐含波动率（Brent 法）。"""
    from scipy.optimize import brentq

    def f(vol):
        return black_caplet(forward, strike, vol, t, tau, df, notional, kind) - price

    return float(brentq(f, 1e-6, 5.0, xtol=1e-10))
