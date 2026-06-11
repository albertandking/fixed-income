"""利率期限结构：bootstrap 与插值。

本模块为骨架占位：函数签名已给出，具体实现随各章撰写补全。
"""

from __future__ import annotations


def bootstrap(instruments):
    """由附息债/零息债报价 bootstrap 即期利率曲线。"""
    raise NotImplementedError("待撰写：见对应章节")


def interpolate(curve, t, method="linear"):
    """对即期曲线在期限 t 处插值（线性/样条）。"""
    raise NotImplementedError("待撰写：见对应章节")
