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
    """牛顿迭代法由价格反解到期收益率，收敛失败时回退二分法。"""
    cashflows = np.asarray(cashflows, dtype=float)
    times = np.asarray(times, dtype=float)

    y = float(guess)
    for _ in range(maxiter):
        base = 1.0 + y / freq
        p = float(np.sum(cashflows * base ** (-freq * times)))
        dp = float(np.sum(cashflows * (-times) * base ** (-freq * times - 1)))
        diff = p - price
        if abs(diff) < tol:
            return y
        if dp == 0:
            break
        y -= diff / dp

    # 回退：二分法
    lo, hi = -0.99 * freq, 1.0
    mid = guess
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        p = price_bond(cashflows, times, mid, freq)
        if abs(p - price) < tol:
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
