"""可转换债券定价：股票二叉树（CRR）+ 反向归纳。

可转债 = 纯债 + 转股权（一个嵌入的股票看涨期权）。本模块用 Cox-Ross-Rubinstein
股票二叉树，对可转债做风险中性反向归纳：

- 到期：:math:`V=\\max(\\text{面值}+\\text{票息},\\ \\text{转股比例}\\times S_T)`；
- 中间节点：:math:`V=\\max(\\underbrace{\\text{转股价值}}_{\\text{ratio}\\times S},\\ \\underbrace{\\text{持有价值}}_{\\text{折现期望}+\\text{票息}})`；
- 可赎回（强赎）：发行人在持有价值过高时赎回，投资者被迫在转股与赎回价间取优；
- 可回售：投资者在价值过低时回售，价值有下限。

为教学清晰，全树用无风险利率折现（简化模型）；纯债价值另用含信用利差的折现率单独计算。
"""

from __future__ import annotations

import numpy as np


def bond_floor(face, coupon_rate, maturity, discount_rate, freq: int = 1) -> float:
    """纯债价值（bond floor）：忽略转股权，按含信用利差的折现率给债券现金流定价。"""
    n = int(round(maturity * freq))
    c = face * coupon_rate / freq
    i = discount_rate / freq
    pv = sum(c / (1 + i) ** j for j in range(1, n + 1))
    return pv + face / (1 + i) ** n


def price_convertible(s0, sigma, r, maturity, face, coupon_rate, conv_ratio,
                      n_steps: int = 100, call_price=None, put_price=None) -> dict:
    """用 CRR 股票二叉树为可转债定价（反向归纳）。

    Parameters
    ----------
    s0 : float
        当前股价。
    sigma : float
        股票波动率。
    r : float
        无风险利率（连续复利近似，用于风险中性概率与折现）。
    maturity, face, coupon_rate, conv_ratio : float
        到期年限、面值、年票息率、转股比例（= 面值 / 转股价）。
    n_steps : int
        二叉树步数。
    call_price, put_price : float, optional
        赎回价 / 回售价（每节点适用的简化处理）；None 表示无此条款。

    Returns
    -------
    dict
        ``price``（可转债价值）、``conversion_value``（当前转股价值）、``stock_tree_u/d/p``。
    """
    dt = maturity / n_steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    disc = np.exp(-r * dt)
    p = (np.exp(r * dt) - d) / (u - d)
    coupon = face * coupon_rate * dt          # 每步票息（按步长摊）

    # 终值：到期日各节点股价与可转债价值
    j = np.arange(n_steps + 1)
    s_t = s0 * u ** (n_steps - j) * d ** j
    v = np.maximum(face + coupon, conv_ratio * s_t)

    for i in range(n_steps - 1, -1, -1):
        j = np.arange(i + 1)
        s = s0 * u ** (i - j) * d ** j
        hold = disc * (p * v[:-1] + (1 - p) * v[1:]) + coupon
        conv = conv_ratio * s
        val = np.maximum(conv, hold)
        if call_price is not None and i > 0:
            # 发行人赎回：投资者在赎回价与转股价值间取优（强赎促转股）
            val = np.minimum(val, np.maximum(call_price, conv))
        if put_price is not None and i > 0:
            val = np.maximum(val, put_price)
        v = val

    return {
        "price": float(v[0]),
        "conversion_value": float(conv_ratio * s0),
        "u": float(u), "d": float(d), "p": float(p),
    }
