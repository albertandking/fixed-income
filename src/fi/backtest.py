"""债券策略回测框架与绩效归因。

本模块为骨架占位：函数签名已给出，具体实现随各章撰写补全。
"""

from __future__ import annotations


def run_backtest(strategy, data):
    """在历史数据上运行债券策略回测。"""
    raise NotImplementedError("待撰写：见对应章节")


def performance(returns):
    """计算绩效指标（年化收益、波动、夏普、最大回撤）。"""
    raise NotImplementedError("待撰写：见对应章节")


def attribution(positions, curve_changes):
    """收益归因（carry/roll-down/久期/利差）。"""
    raise NotImplementedError("待撰写：见对应章节")
