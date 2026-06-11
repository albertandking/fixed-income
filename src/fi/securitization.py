"""资产证券化（ABS/MBS）：分层、损失分配与现金流瀑布。

结构化产品把一个资产池的现金流按优先级**分层（tranching）**再分配：损失自下而上
（次级先吸收）由各档承担，这种**次级垫底**正是对优先档的信用增级。

- :func:`attachment_detachment` 给出各档的附着/脱离点（损失占资产池的百分比区间）；
- :func:`allocate_losses` 把资产池损失自下而上分配到各档；
- :func:`sequential_waterfall` 模拟逐期"利息瀑布 + 顺序还本"的现金流分配。
"""

from __future__ import annotations

import numpy as np


def attachment_detachment(tranches):
    """各档的附着点/脱离点（占资产池的损失百分比）。

    Parameters
    ----------
    tranches : list[tuple[str, float]]
        ``[(名称, 规模), ...]``，按**优先级从高到低**（优先档在前、次级档在后）。

    Returns
    -------
    list[dict]
        每档的 ``name``、``attach``、``detach``（自下而上累积的损失占比区间）。
    """
    total = sum(sz for _, sz in tranches)
    out = []
    # 自下而上（次级先吸收损失）累积
    cum = 0.0
    bottom_up = list(reversed(tranches))
    info = {}
    for name, sz in bottom_up:
        attach = cum / total
        cum += sz
        detach = cum / total
        info[name] = {"name": name, "attach": attach, "detach": detach}
    # 按原优先级顺序输出
    for name, _ in tranches:
        out.append(info[name])
    return out


def allocate_losses(pool_loss, tranches):
    """把资产池损失（绝对金额）自下而上分配到各档（次级先吸收）。

    Returns
    -------
    dict
        每档 ``{名称: 损失金额}``。
    """
    remaining = float(pool_loss)
    result = {}
    for name, size in reversed(tranches):     # 次级先吸收
        absorbed = min(size, remaining)
        result[name] = absorbed
        remaining -= absorbed
    return result


def sequential_waterfall(pool_cashflows, tranches, tranche_rates, dt: float = 1.0):
    """逐期顺序支付瀑布：先付各档利息（优先级从高到低），再顺序偿还本金。

    Parameters
    ----------
    pool_cashflows : array-like
        每期资产池可分配现金（已扣违约、含回收）。
    tranches : list[tuple[str, float]]
        ``[(名称, 初始本金), ...]``，优先级从高到低。
    tranche_rates : list[float]
        各档票面利率（年化），与 ``tranches`` 对应。
    dt : float
        每期年化分数（默认 1）。

    Returns
    -------
    dict
        每档收到的 ``interest`` 与 ``principal`` 现金流序列，及期末未偿本金 ``shortfall``。
    """
    names = [n for n, _ in tranches]
    bal = {n: float(sz) for n, sz in tranches}
    rate = dict(zip(names, tranche_rates))
    paid_int = {n: [] for n in names}
    paid_prin = {n: [] for n in names}

    for cash in pool_cashflows:
        avail = float(cash)
        # 利息瀑布：优先级从高到低
        for n in names:
            due = bal[n] * rate[n] * dt
            pay = min(avail, due)
            paid_int[n].append(pay)
            avail -= pay
        # 还本瀑布：顺序偿还（优先档先还完）
        prin_this = {n: 0.0 for n in names}
        for n in names:
            pay = min(avail, bal[n])
            prin_this[n] += pay
            bal[n] -= pay
            avail -= pay
        for n in names:
            paid_prin[n].append(prin_this[n])

    return {
        "interest": paid_int,
        "principal": paid_prin,
        "shortfall": {n: bal[n] for n in names},   # 期末未偿本金（损失）
    }
