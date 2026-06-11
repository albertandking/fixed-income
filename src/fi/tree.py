"""利率二叉树与含权债定价（反向归纳）。

构建一棵重组的对数正态短期利率树，用风险中性（概率 0.5）反向归纳为债券定价：

- 普通债：每个节点价值 = (票息 + 期望后续价值) 折现；
- **可赎回债**：发行人在续作价值高于赎回价时赎回 → 节点价值取 ``min(续作, 赎回价)``；
- **可回售债**：投资者在续作价值低于回售价时回售 → 节点价值取 ``max(续作, 回售价)``。

含权债价值与普通债价值之差，即**嵌入期权的价值**。
"""

from __future__ import annotations

import numpy as np


def short_rate_tree(r0: float, sigma: float, n_steps: int, dt: float = 1.0):
    """构建一棵重组对数正态短期利率树（围绕 r0、波动率 sigma 对称）。

    节点 ``(i, j)``（第 i 步、j 次下移）的短期利率
    :math:`r_{i,j}=r_0\\exp[\\sigma\\sqrt{dt}\\,(i-2j)]`：j=0 全上行（最高），j=i 全下行（最低）。
    """
    tree = []
    for i in range(n_steps):
        row = [r0 * np.exp(sigma * np.sqrt(dt) * (i - 2 * j)) for j in range(i + 1)]
        tree.append(row)
    return tree


def value_bond(tree, coupon, face: float = 100.0, dt: float = 1.0,
               call_price: float | None = None, call_from: int | None = None,
               put_price: float | None = None, put_from: int | None = None,
               prob: float = 0.5) -> float:
    """反向归纳为（含权）债券定价，返回根节点价值。

    Parameters
    ----------
    tree : list[list[float]]
        短期利率树，``tree[i][j]`` 为节点 (i,j) 的单期利率，共 ``n=len(tree)`` 步，到期在第 n 步。
    coupon : float
        每期票息（金额，非利率）。
    call_price, call_from : float, int
        赎回价与开始可赎回的步数（含）；为 None 表示不可赎回。
    put_price, put_from : float, int
        回售价与开始可回售的步数（含）；为 None 表示不可回售。
    """
    n = len(tree)
    V = [face] * (n + 1)                      # 到期日各节点：偿还本金
    for i in range(n - 1, -1, -1):
        new_v = []
        for j in range(i + 1):
            r = tree[i][j]
            cont = (coupon + prob * V[j] + (1 - prob) * V[j + 1]) / (1 + r * dt)
            val = cont
            if call_price is not None and call_from is not None and i >= call_from and i > 0:
                val = min(val, call_price)    # 发行人赎回
            if put_price is not None and put_from is not None and i >= put_from and i > 0:
                val = max(val, put_price)     # 投资者回售
            new_v.append(val)
        V = new_v
    return V[0]


def effective_duration_tree(r0, sigma, n_steps, coupon, face=100.0, dt=1.0,
                            dy=1e-3, **kwargs) -> float:
    """含权债的有效久期：整体平移短期利率树 ±dy 重新定价的数值差商。"""
    p0 = value_bond(short_rate_tree(r0, sigma, n_steps, dt), coupon, face, dt, **kwargs)
    pu = value_bond(short_rate_tree(r0 + dy, sigma, n_steps, dt), coupon, face, dt, **kwargs)
    pd = value_bond(short_rate_tree(r0 - dy, sigma, n_steps, dt), coupon, face, dt, **kwargs)
    return (pd - pu) / (2 * p0 * dy)


def effective_convexity_tree(r0, sigma, n_steps, coupon, face=100.0, dt=1.0,
                             dy=1e-3, **kwargs) -> float:
    """含权债的有效凸性（可为负——可赎回债的负凸性）。"""
    p0 = value_bond(short_rate_tree(r0, sigma, n_steps, dt), coupon, face, dt, **kwargs)
    pu = value_bond(short_rate_tree(r0 + dy, sigma, n_steps, dt), coupon, face, dt, **kwargs)
    pd = value_bond(short_rate_tree(r0 - dy, sigma, n_steps, dt), coupon, face, dt, **kwargs)
    return (pu + pd - 2 * p0) / (p0 * dy ** 2)
