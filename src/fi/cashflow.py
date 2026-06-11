"""货币时间价值、计息惯例（day count）、现金流与应计利息。

时间价值采用每年复利 ``freq`` 次的离散复利；计息惯例支持 ACT/ACT、
ACT/365、ACT/360、30/360。应计利息按"已计息期间 / 完整付息期间"折算当期票息。
"""

from __future__ import annotations

import datetime as dt

import numpy as np

# ---------------------------------------------------------------------------
# 货币时间价值
# ---------------------------------------------------------------------------

def future_value(pv: float, rate: float, years: float, freq: int = 1) -> float:
    r"""终值：:math:`FV=PV(1+r/k)^{k t}`。"""
    return pv * (1.0 + rate / freq) ** (freq * years)


def present_value(fv: float, rate: float, years: float, freq: int = 1) -> float:
    r"""现值：:math:`PV=FV(1+r/k)^{-k t}`。"""
    return fv * (1.0 + rate / freq) ** (-freq * years)


def annuity_pv(payment: float, rate: float, n_periods: int, freq: int = 1) -> float:
    r"""普通年金现值：每期末支付 ``payment``，共 ``n_periods`` 期，每期利率 :math:`r/k`。

    :math:`PV=\text{pmt}\cdot\dfrac{1-(1+r/k)^{-N}}{r/k}`
    """
    i = rate / freq
    if i == 0:
        return payment * n_periods
    return payment * (1.0 - (1.0 + i) ** (-n_periods)) / i


def annuity_payment(pv: float, rate: float, n_periods: int, freq: int = 1) -> float:
    r"""由现值反解等额年金（等额本息还款额）：:math:`\text{pmt}=PV\cdot\dfrac{r/k}{1-(1+r/k)^{-N}}`。"""
    i = rate / freq
    if i == 0:
        return pv / n_periods
    return pv * i / (1.0 - (1.0 + i) ** (-n_periods))


# ---------------------------------------------------------------------------
# 计息惯例（Day Count Conventions）
# ---------------------------------------------------------------------------

def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days(start: dt.date, end: dt.date) -> int:
    return (end - start).days


def year_fraction(start: dt.date, end: dt.date, convention: str = "ACT/ACT") -> float:
    """按计息惯例计算两个日期之间的计息年化分数。

    支持 ``ACT/ACT``（ISDA，按日历年拆分）、``ACT/365``、``ACT/360``、``30/360``。
    """
    if start == end:
        return 0.0
    if start > end:
        return -year_fraction(end, start, convention)

    conv = convention.upper().replace(" ", "").replace("ACTUAL", "ACT")

    if conv in ("ACT/365", "ACT/365F"):
        return _days(start, end) / 365.0
    if conv == "ACT/360":
        return _days(start, end) / 360.0
    if conv in ("30/360", "30/360US", "30E/360"):
        d1, d2 = min(start.day, 30), end.day
        if d1 == 30 and d2 == 31:
            d2 = 30
        return ((end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)) / 360.0
    if conv in ("ACT/ACT", "ACT/ACTISDA"):
        total = 0.0
        for y in range(start.year, end.year + 1):
            seg_start = max(start, dt.date(y, 1, 1))
            seg_end = min(end, dt.date(y + 1, 1, 1))
            if seg_end > seg_start:
                total += _days(seg_start, seg_end) / (366.0 if _is_leap(y) else 365.0)
        return total
    raise ValueError(f"未知计息惯例: {convention}")


# ---------------------------------------------------------------------------
# 现金流与应计利息
# ---------------------------------------------------------------------------

def accrued_interest(settle: dt.date, prev_coupon: dt.date, next_coupon: dt.date,
                     coupon_rate: float, freq: int = 2, face: float = 100.0,
                     convention: str = "ACT/ACT") -> float:
    """结算日的应计利息：当期票息 × 已计息期间 / 完整付息期间。

    Parameters
    ----------
    settle, prev_coupon, next_coupon : datetime.date
        结算日、上一付息日、下一付息日。
    coupon_rate : float
        年化票面利率（如 0.03）。
    freq, face : int, float
        每年付息次数、面值。
    convention : str
        计息惯例，传给 :func:`year_fraction`。
    """
    coupon = face * coupon_rate / freq
    period = year_fraction(prev_coupon, next_coupon, convention)
    accrued = year_fraction(prev_coupon, settle, convention)
    return coupon * accrued / period


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
