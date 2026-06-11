"""国债期货与远期：转换因子、最便宜可交割券（CTD）、套保比率与 FRA。

国债期货以"名义标准券"（中金所名义票息 3%）报价，实际可交割多只券，用**转换因子**
把各券折算到名义券。卖方会选择交割成本最低的券——**最便宜可交割券（CTD）**。
"""

from __future__ import annotations

from .cashflow import make_cashflows
from .pricing import price_bond
from .risk import dv01 as _dv01


def conversion_factor(coupon_rate, years_to_maturity, notional: float = 0.03,
                      freq: int = 1, face: float = 100.0) -> float:
    """转换因子：把可交割券按名义票息（默认 3%）折算到名义标准券。

    概念定义 = 该券以名义票息为收益率定价所得的每元面值净价。
    票息 > 名义票息 → CF > 1；票息 < 名义票息 → CF < 1。
    """
    cf, t = make_cashflows(coupon_rate, years_to_maturity, freq, face)
    return price_bond(cf, t, notional, freq) / face


def ctd(bonds, futures_price):
    """从可交割券集合中确定最便宜可交割券（CTD）。

    Parameters
    ----------
    bonds : list[dict]
        每只券 ``{'name', 'clean_price', 'conversion_factor'}``。
    futures_price : float
        期货价格。

    Returns
    -------
    (best, table) : tuple[dict, list[dict]]
        CTD 券，及各券的毛基差 ``gross_basis = 净价 - 期货价 × CF``（越小越便宜交割）。
    """
    table = []
    for b in bonds:
        gb = b["clean_price"] - futures_price * b["conversion_factor"]
        table.append({**b, "gross_basis": gb})
    best = min(table, key=lambda x: x["gross_basis"])
    return best, table


def futures_dv01(ctd_dv01, ctd_cf) -> float:
    """期货 DV01 ≈ CTD 的 DV01 / CTD 的转换因子。"""
    return ctd_dv01 / ctd_cf


def hedge_ratio(portfolio_dv01, ctd_dv01, ctd_cf) -> float:
    """久期中性（DV01 中性）套保所需的期货合约数。

    :math:`N=-\\dfrac{\\text{组合 DV01}}{\\text{期货 DV01}}`，负号表示多头组合需卖出期货。
    """
    return -portfolio_dv01 / futures_dv01(ctd_dv01, ctd_cf)


def fra_value(notional, contract_rate, forward_rate, tau, discount_factor=1.0) -> float:
    """远期利率协议（FRA）对**多头（付固定、收浮动）**的价值。

    :math:`V=\\text{名义}\\times(\\text{远期}-\\text{合约利率})\\times\\tau\\times DF`。
    """
    return notional * (forward_rate - contract_rate) * tau * discount_factor


def bond_dv01(coupon_rate, years_to_maturity, ytm, freq: int = 1, face: float = 100.0) -> float:
    """便捷函数：由票息/期限/收益率算债券 DV01（复用 fi.risk）。"""
    cf, t = make_cashflows(coupon_rate, years_to_maturity, freq, face)
    return _dv01(cf, t, ytm, freq)
