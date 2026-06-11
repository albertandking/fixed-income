"""回购与货币市场：回购现金流、资金成本、杠杆与套息（carry）测算。

中国银行间回购利息按 **实际天数 / 365（ACT/365）单利**计算：

.. math::  I = \\text{本金}\\times r\\times \\frac{\\text{天数}}{365}

杠杆套息的核心恒等式（忽略价格变动的纯 carry 视角）：

.. math::  \\text{ROE} = y + (L-1)(y-r)

其中 :math:`y` 为持有债券收益率，:math:`r` 为回购融资利率，
:math:`L=1/\\text{haircut}` 为最大杠杆倍数。
"""

from __future__ import annotations


def repo_interest(principal: float, rate: float, days: int, basis: int = 365) -> float:
    """回购利息（ACT/365 单利）。``rate`` 为年化利率（如 0.0185）。"""
    return principal * rate * days / basis


def repo_cashflows(principal: float, rate: float, days: int, basis: int = 365) -> dict:
    """正回购（融资方）现金流：首期拿到本金，到期偿还本金 + 利息。

    Returns
    -------
    dict
        ``day0_in`` 首期现金流入、``dayN_out`` 到期现金流出、``interest`` 利息。
    """
    interest = repo_interest(principal, rate, days, basis)
    return {"day0_in": principal, "dayN_out": principal + interest, "interest": interest}


def max_leverage(haircut: float) -> float:
    """由折扣率（haircut）得到理论最大杠杆 :math:`L=1/\\text{haircut}`。"""
    return 1.0 / haircut


def leveraged_carry(bond_yield: float, repo_rate: float,
                    leverage: float, holding_years: float = 1.0) -> dict:
    """杠杆套息的权益回报（纯 carry 视角，不含债券价格变动）。

    Parameters
    ----------
    bond_yield : float
        持有债券的年化收益率 :math:`y`。
    repo_rate : float
        回购融资年化利率 :math:`r`。
    leverage : float
        实际杠杆倍数 :math:`L=` 总资产 / 自有权益。
    holding_years : float
        持有期（年），用于把年化 ROE 折算到持有期。

    Returns
    -------
    dict
        ``carry_spread`` (= y - r)、``roe_annual``、``roe_period``。
    """
    carry_spread = bond_yield - repo_rate
    roe_annual = bond_yield + (leverage - 1.0) * carry_spread
    return {
        "carry_spread": carry_spread,
        "roe_annual": roe_annual,
        "roe_period": roe_annual * holding_years,
    }
