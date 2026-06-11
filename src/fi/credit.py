"""信用风险：结构化模型（Merton/KMV）与约化模型。

本模块为骨架占位：函数签名已给出，具体实现随各章撰写补全。
"""

from __future__ import annotations


def merton_pd(asset_value, debt, asset_vol, r, t):
    """Merton 模型计算违约距离与违约概率。"""
    raise NotImplementedError("待撰写：见对应章节")


def hazard_from_spread(spread, recovery=0.4):
    """由信用利差反推违约强度/隐含违约率。"""
    raise NotImplementedError("待撰写：见对应章节")


def survival_probability(hazard_curve, t):
    """由强度曲线计算生存概率。"""
    raise NotImplementedError("待撰写：见对应章节")
