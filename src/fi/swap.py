"""利率互换（IRS）：平价互换利率、互换估值、DV01 与互换曲线 bootstrap。

普通利率互换一方付固定、收浮动。在标准（浮动腿按曲线重置）假设下：

- 浮动腿现值 = 名义 × (1 − DF(T_n))；
- 固定腿现值 = 名义 × 固定利率 × Σ τ_i DF(T_i)（年金）；
- **平价互换利率**使互换初始价值为零：:math:`s=\\dfrac{1-DF(T_n)}{\\sum_i \\tau_i DF(T_i)}`。

注：平价互换利率与平价票息率同形，故由互换报价 bootstrap 折现因子，与债券 bootstrap 一致。
"""

from __future__ import annotations

import numpy as np


def annuity(discount_factors, taus) -> float:
    """固定腿年金因子 :math:`\\sum_i \\tau_i DF(T_i)`。"""
    df = np.asarray(discount_factors, dtype=float)
    tau = np.asarray(taus, dtype=float)
    return float(np.sum(tau * df))


def par_swap_rate(discount_factors, taus) -> float:
    """平价互换利率：使互换初始价值为零的固定利率。"""
    df = np.asarray(discount_factors, dtype=float)
    return float((1.0 - df[-1]) / annuity(df, taus))


def swap_value(fixed_rate, discount_factors, taus, notional: float = 1e8, payer: bool = True) -> float:
    """互换价值（payer = 付固定、收浮动）。

    :math:`V_{payer}=\\text{名义}\\,[(1-DF(T_n)) - s\\sum_i\\tau_i DF_i]`。
    """
    df = np.asarray(discount_factors, dtype=float)
    fixed_pv = fixed_rate * annuity(df, taus) * notional
    float_pv = (1.0 - df[-1]) * notional
    val = float_pv - fixed_pv
    return float(val if payer else -val)


def swap_dv01(discount_factors, taus, notional: float = 1e8) -> float:
    """互换 DV01（固定腿 PV01）：固定利率变动 1bp 的价值变化 ≈ 年金 × 名义 × 1e-4。"""
    return annuity(discount_factors, taus) * notional * 1e-4


def bootstrap_swap_curve(par_rates):
    """由整数年期限的平价互换利率 bootstrap 折现因子与零息（即期）利率。

    与债券 par 曲线 bootstrap 同形：``1 = s_n Σ_{j<n} DF_j + (1+s_n) DF_n``。

    Returns
    -------
    (zeros, discount_factors) : tuple[numpy.ndarray, numpy.ndarray]
    """
    s = np.asarray(par_rates, dtype=float)
    n_total = len(s)
    dfs = np.zeros(n_total)
    zeros = np.zeros(n_total)
    for n in range(1, n_total + 1):
        c = s[n - 1]
        df_n = (1.0 - c * dfs[: n - 1].sum()) / (1.0 + c)
        dfs[n - 1] = df_n
        zeros[n - 1] = df_n ** (-1.0 / n) - 1.0
    return zeros, dfs
