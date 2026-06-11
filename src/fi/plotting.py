"""统一的中文绘图样式。

在每章 notebook 顶部调用 :func:`use_chinese_style` 即可正常显示中文与负号。
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

# 优先尝试的中文字体（按平台常见字体排序）
_CJK_FONTS = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "PingFang SC", "Arial Unicode MS"]


def use_chinese_style() -> None:
    """设置 matplotlib 以正确显示中文与负号，并应用统一风格。"""
    mpl.rcParams["font.sans-serif"] = _CJK_FONTS
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["figure.dpi"] = 110
    mpl.rcParams["savefig.bbox"] = "tight"
    mpl.rcParams["axes.grid"] = True
    mpl.rcParams["grid.alpha"] = 0.3


def new_axes(figsize: tuple[float, float] = (8, 4.5)):
    """返回应用统一风格后的 ``(fig, ax)``。"""
    use_chinese_style()
    return plt.subplots(figsize=figsize)
