"""现金流、计息惯例与应计利息。

本模块为骨架占位：函数签名已给出，具体实现随各章撰写补全。
"""

from __future__ import annotations

import numpy as np


def year_fraction(start, end, convention="ACT/ACT"):
    """按计息惯例计算计息年化分数（ACT/ACT、30/360、ACT/365 等）。"""
    raise NotImplementedError("待撰写：见第2章")


def accrued_interest(settle, schedule, coupon, face=100.0, convention="ACT/ACT"):
    """计算结算日的应计利息。"""
    raise NotImplementedError("待撰写：见第2章")


def make_cashflows(coupon_rate, maturity, freq: int = 2, face: float = 100.0):
    """生成一只到期一次还本（子弹型）附息债的现金流与时间。

    Parameters
    ----------
    coupon_rate : float
        年化票面利率（如 0.03 表示 3%）。
    maturity : float
        剩余期限（年）。
    freq : int
        每年付息次数（默认 2）。
    face : float
        面值（默认 100）。

    Returns
    -------
    (cashflows, times) : tuple[numpy.ndarray, numpy.ndarray]
        现金流序列及其对应时间（年）；末期含还本。
    """
    n = int(round(maturity * freq))
    if n <= 0:
        # 不足一个付息周期：退化为到期日的单笔本金（含末期票息）兑付
        coupon = face * coupon_rate / freq if maturity > 0 else 0.0
        return np.array([face + coupon], dtype=float), np.array([max(maturity, 0.0)], dtype=float)
    times = np.array([(i + 1) / freq for i in range(n)], dtype=float)
    coupon = face * coupon_rate / freq
    cashflows = np.full(n, coupon, dtype=float)
    cashflows[-1] += face
    return cashflows, times
