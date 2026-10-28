"""债券定价、到期收益率与即期/远期利率。

约定：现金流 ``cashflows`` 与对应时间 ``times``（单位：年）一一对应；
``ytm`` 为年化到期收益率，``freq`` 为每年付息/复利次数（默认 2）。
折现采用 :math:`P=\\sum_i CF_i\\,(1+y/k)^{-k t_i}`。
"""

from __future__ import annotations

import numpy as np


def price_bond(cashflows, times, ytm, freq: int = 2) -> float:
    """给定到期收益率，对现金流折现求债券（全价）。"""
    cashflows = np.asarray(cashflows, dtype=float)
    times = np.asarray(times, dtype=float)
    df = (1.0 + ytm / freq) ** (-freq * times)
    return float(np.sum(cashflows * df))


def ytm(price, cashflows, times, freq: int = 2, guess: float = 0.03,
        tol: float = 1e-12, maxiter: int = 100) -> float:
    """由价格反解到期收益率：先用牛顿迭代，未收敛时回退二分法。

    合法域为 :math:`y>-k`（``k = freq``）。二分回退先确认区间夹住根：下端取
    ``-0.99*freq``，上端自 1.0 起逐次加倍直至价格低于目标价；若无法夹根
    （目标价超出可达范围或价格非正），抛出 ``ValueError`` 而不返回端点值。
    """
    cashflows = np.asarray(cashflows, dtype=float)
    times = np.asarray(times, dtype=float)
    if price <= 0:
        raise ValueError("价格必须为正")

    y = float(guess)
    for _ in range(maxiter):
        if not np.isfinite(y) or y <= -freq:
            break                       # 迭代越出合法域，转二分法
        base = 1.0 + y / freq
        p = float(np.sum(cashflows * base ** (-freq * times)))
        dp = float(np.sum(cashflows * (-times) * base ** (-freq * times - 1)))
        diff = p - price
        if abs(diff) < tol:
            return y
        if dp == 0 or not np.isfinite(dp):
            break
        y -= diff / dp

    # 回退：二分法（先夹根）
    lo, hi = -0.99 * freq, 1.0
    if price_bond(cashflows, times, lo, freq) < price:
        raise ValueError(f"目标价格 {price} 高于收益率 {lo} 处的价格，无法在合法域内求解")
    while price_bond(cashflows, times, hi, freq) > price:
        hi *= 2.0
        if hi > 1e6:
            raise ValueError(f"目标价格 {price} 过低，未能在收益率 1e6 以内夹住根")
    mid = 0.5 * (lo + hi)
    for _ in range(500):
        mid = 0.5 * (lo + hi)
        p = price_bond(cashflows, times, mid, freq)
        if abs(p - price) < tol or hi - lo < 1e-15:
            return mid
        if p > price:      # 价格偏高 → 收益率偏低 → 提高下界
            lo = mid
        else:
            hi = mid
    return mid


def forward_rate(spot_curve, t1: float, t2: float, freq: int = 1) -> float:
    """由即期利率曲线计算 t1->t2 的（离散复利）远期利率。

    ``spot_curve`` 为 期限 t（年）-> 即期利率 的可调用对象。
    """
    z1, z2 = spot_curve(t1), spot_curve(t2)
    df1 = (1.0 + z1 / freq) ** (-freq * t1)
    df2 = (1.0 + z2 / freq) ** (-freq * t2)
    return freq * ((df1 / df2) ** (1.0 / (freq * (t2 - t1))) - 1.0)


def current_yield(annual_coupon: float, price: float) -> float:
    """当期收益率（current yield）：年票息 / 市价。仅反映票息回报，忽略资本利得与再投资。"""
    return annual_coupon / price
