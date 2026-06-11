"""利率期限结构：由平价票息曲线 bootstrap 即期（零息）利率，并提供插值。

约定：整数年期限、每年付息一次（年付息）的平价附息债，面值归一为 1。
平价债价格 = 1，票面利率 = 平价收益率。逐期剥离折现因子：

.. math::
   1 = c_n\\sum_{j=1}^{n-1} DF_j + (1+c_n)\\,DF_n
   \\;\\Longrightarrow\\;
   DF_n = \\frac{1 - c_n\\sum_{j=1}^{n-1} DF_j}{1+c_n},
   \\quad z_n = DF_n^{-1/n} - 1
"""

from __future__ import annotations

import numpy as np


def bootstrap(par_yields):
    """从整数年期限的平价票息率 bootstrap 即期（零息）利率与折现因子。

    Parameters
    ----------
    par_yields : array-like
        ``par_yields[k]`` 为期限 ``k+1`` 年的平价收益率（年付息），共 ``N`` 个，期限 1..N。

    Returns
    -------
    (zeros, discount_factors) : tuple[numpy.ndarray, numpy.ndarray]
        即期利率与对应的折现因子，长度 ``N``，对应期限 1..N（年）。
    """
    y = np.asarray(par_yields, dtype=float)
    n_total = len(y)
    dfs = np.zeros(n_total)
    zeros = np.zeros(n_total)
    for n in range(1, n_total + 1):
        c = y[n - 1]
        coupon_pv = c * dfs[: n - 1].sum()
        df_n = (1.0 - coupon_pv) / (1.0 + c)
        dfs[n - 1] = df_n
        zeros[n - 1] = df_n ** (-1.0 / n) - 1.0
    return zeros, dfs


def interpolate(tenors, values, t, method: str = "linear"):
    """在给定节点 ``(tenors, values)`` 上对期限 ``t`` 处插值。

    ``method``：``"linear"``（分段线性）或 ``"cubic"``（三次样条，需要 scipy）。
    ``t`` 可为标量或数组。
    """
    tenors = np.asarray(tenors, dtype=float)
    values = np.asarray(values, dtype=float)
    if method == "linear":
        return np.interp(t, tenors, values)
    if method == "cubic":
        from scipy.interpolate import CubicSpline

        return CubicSpline(tenors, values)(t)
    raise ValueError(f"未知插值方法: {method}")


def forward_curve(zeros, tenors=None, freq: int = 1):
    """由即期利率序列计算相邻期限之间的（离散复利）远期利率。

    Parameters
    ----------
    zeros : array-like
        即期利率，对应 ``tenors``（默认为 1..N 年）。
    tenors : array-like, optional
        期限（年）。默认 ``[1, 2, ..., N]``。

    Returns
    -------
    (mid_tenors, forwards) : tuple[numpy.ndarray, numpy.ndarray]
        各相邻区间右端点期限及其远期利率。
    """
    zeros = np.asarray(zeros, dtype=float)
    if tenors is None:
        tenors = np.arange(1, len(zeros) + 1, dtype=float)
    else:
        tenors = np.asarray(tenors, dtype=float)
    fwd_t, fwd = [], []
    for i in range(1, len(tenors)):
        t1, t2 = tenors[i - 1], tenors[i]
        z1, z2 = zeros[i - 1], zeros[i]
        df1 = (1.0 + z1 / freq) ** (-freq * t1)
        df2 = (1.0 + z2 / freq) ** (-freq * t2)
        fwd_t.append(t2)
        fwd.append(freq * ((df1 / df2) ** (1.0 / (freq * (t2 - t1))) - 1.0))
    return np.asarray(fwd_t), np.asarray(fwd)
