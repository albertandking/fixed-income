"""债券组合管理：组合久期、久期匹配（免疫）与现金流匹配（专用组合）。

- :func:`portfolio_duration` 按市值加权汇总组合久期；
- :func:`two_asset_immunization` 用两只债（哑铃）匹配目标久期；
- :func:`cash_flow_match` 用线性规划求"以最小成本、各期资产现金流覆盖负债"的专用组合。
"""

from __future__ import annotations

import numpy as np


def portfolio_duration(market_values, durations) -> float:
    """组合修正久期 = 市值加权平均久期。"""
    mv = np.asarray(market_values, dtype=float)
    d = np.asarray(durations, dtype=float)
    return float(np.sum(mv * d) / np.sum(mv))


def two_asset_immunization(d_short: float, d_long: float, d_target: float):
    """用一只短久期债与一只长久期债（哑铃）匹配目标久期。

    解 :math:`w_s d_s + w_l d_l = d_{target}`、:math:`w_s + w_l = 1`。

    Returns
    -------
    (w_short, w_long) : tuple[float, float]
        两只债的市值权重（可能需校验非负）。
    """
    w_long = (d_target - d_short) / (d_long - d_short)
    return 1.0 - w_long, w_long


def cash_flow_match(liabilities, bond_cashflows, bond_prices):
    """现金流匹配：最小成本买入债券，使各期资产现金流不低于负债。

    .. math::
        \\min_x\\; p^\\top x \\quad\\text{s.t.}\\quad C^\\top x \\ge \\ell,\\; x \\ge 0

    Parameters
    ----------
    liabilities : array-like, shape (T,)
        各期负债现金流 :math:`\\ell_t`。
    bond_cashflows : array-like, shape (n_bonds, T)
        每只债在各期的现金流 :math:`C`。
    bond_prices : array-like, shape (n_bonds,)
        每只债的单位价格 :math:`p`。

    Returns
    -------
    dict
        ``units``（各债买入份数）、``cost``（总成本）、``success``（是否求解成功）。
    """
    from scipy.optimize import linprog

    liabilities = np.asarray(liabilities, dtype=float)
    C = np.asarray(bond_cashflows, dtype=float)      # (n_bonds, T)
    p = np.asarray(bond_prices, dtype=float)

    # C^T x >= ell  ->  -C^T x <= -ell
    A_ub = -C.T                                       # (T, n_bonds)
    b_ub = -liabilities
    res = linprog(c=p, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method="highs")
    return {
        "units": res.x if res.success else None,
        "cost": float(res.fun) if res.success else None,
        "success": bool(res.success),
    }
