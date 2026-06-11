"""利率风险度量：久期、凸性、DV01、关键利率久期。

记号与 :mod:`fi.pricing` 一致：现金流 ``cashflows`` 与时间 ``times``（年）一一对应，
``ytm`` 为年化收益率，``freq`` 为每年付息次数，折现因子 :math:`(1+y/k)^{-k t}`。
"""

from __future__ import annotations

import numpy as np

from .pricing import price_bond


def _pv(cashflows, times, ytm, freq):
    cashflows = np.asarray(cashflows, dtype=float)
    times = np.asarray(times, dtype=float)
    df = (1.0 + ytm / freq) ** (-freq * times)
    return cashflows * df, times


def macaulay_duration(cashflows, times, ytm, freq: int = 2) -> float:
    r"""麦考利久期：现金流现值加权的平均回收时间（年）。

    :math:`D_{mac}=\frac{1}{P}\sum_i t_i\cdot CF_i(1+y/k)^{-k t_i}`
    """
    pv, t = _pv(cashflows, times, ytm, freq)
    return float(np.sum(t * pv) / np.sum(pv))


def modified_duration(cashflows, times, ytm, freq: int = 2) -> float:
    r"""修正久期：:math:`D_{mod}=D_{mac}/(1+y/k)`，满足 :math:`\Delta P/P\approx -D_{mod}\,\Delta y`。"""
    return macaulay_duration(cashflows, times, ytm, freq) / (1.0 + ytm / freq)


def convexity(cashflows, times, ytm, freq: int = 2) -> float:
    r"""凸性（解析式）：:math:`C=\frac{1}{P}\sum_i CF_i\,t_i(t_i+1/k)(1+y/k)^{-k t_i-2}`。"""
    cashflows = np.asarray(cashflows, dtype=float)
    times = np.asarray(times, dtype=float)
    p = price_bond(cashflows, times, ytm, freq)
    base = 1.0 + ytm / freq
    terms = cashflows * times * (times + 1.0 / freq) * base ** (-freq * times - 2)
    return float(np.sum(terms) / p)


def dv01(cashflows, times, ytm, freq: int = 2) -> float:
    """基点价值 DV01/PV01：收益率上行 1bp 引起的价格变动绝对值。"""
    p = price_bond(cashflows, times, ytm, freq)
    return modified_duration(cashflows, times, ytm, freq) * p * 1e-4


def price_change(price0: float, mod_dur: float, conv: float, dy: float) -> float:
    r"""久期 + 凸性二阶近似的价格变动：:math:`\Delta P\approx P_0(-D_{mod}\Delta y+\tfrac12 C\Delta y^2)`。"""
    return price0 * (-mod_dur * dy + 0.5 * conv * dy ** 2)


def effective_duration(cashflows, times, ytm, freq: int = 2, dy: float = 1e-4) -> float:
    r"""有效久期：用 :math:`\pm\Delta y` 重新定价的数值差商，适用于含权债等价格非解析的情形。

    :math:`D_{eff}=\dfrac{P_{-}-P_{+}}{2P_0\,\Delta y}`
    """
    p0 = price_bond(cashflows, times, ytm, freq)
    p_up = price_bond(cashflows, times, ytm + dy, freq)
    p_dn = price_bond(cashflows, times, ytm - dy, freq)
    return (p_dn - p_up) / (2.0 * p0 * dy)


def effective_convexity(cashflows, times, ytm, freq: int = 2, dy: float = 1e-4) -> float:
    r"""有效凸性：:math:`C_{eff}=\dfrac{P_{+}+P_{-}-2P_0}{P_0\,\Delta y^2}`。"""
    p0 = price_bond(cashflows, times, ytm, freq)
    p_up = price_bond(cashflows, times, ytm + dy, freq)
    p_dn = price_bond(cashflows, times, ytm - dy, freq)
    return (p_up + p_dn - 2.0 * p0) / (p0 * dy ** 2)


def _price_from_zeros(cashflows, times, key_tenors, zeros):
    """用（连续复利）零息曲线线性插值折现，得到债券价格。"""
    z = np.interp(times, key_tenors, zeros)
    return float(np.sum(np.asarray(cashflows, float) * np.exp(-z * np.asarray(times, float))))


def key_rate_durations(cashflows, times, key_tenors, zeros, dy: float = 1e-4):
    r"""关键利率久期（KRD）：在每个关键期限节点上单独平移零息曲线 :math:`\pm\Delta y`，
    其余节点不变，度量价格对该节点的敏感度。各 KRD 之和近似等于平行移动下的有效久期。

    Returns
    -------
    numpy.ndarray
        与 ``key_tenors`` 等长的 KRD 向量。
    """
    cashflows = np.asarray(cashflows, dtype=float)
    times = np.asarray(times, dtype=float)
    key_tenors = np.asarray(key_tenors, dtype=float)
    zeros = np.asarray(zeros, dtype=float)

    p0 = _price_from_zeros(cashflows, times, key_tenors, zeros)
    out = np.empty_like(key_tenors)
    for i in range(len(key_tenors)):
        zu, zd = zeros.copy(), zeros.copy()
        zu[i] += dy
        zd[i] -= dy
        p_up = _price_from_zeros(cashflows, times, key_tenors, zu)
        p_dn = _price_from_zeros(cashflows, times, key_tenors, zd)
        out[i] = (p_dn - p_up) / (2.0 * p0 * dy)
    return out
