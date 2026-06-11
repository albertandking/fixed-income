"""fi —— 《固定收益证券》全书复用工具包。

正文与各章 notebook 统一通过 ``from fi import ...`` 调用复用逻辑，
避免代码在正文与 notebook 两处维护。各子模块：

- :mod:`fi.data`      数据读取 / 内置离线样本加载
- :mod:`fi.cashflow`  现金流、计息惯例、应计利息
- :mod:`fi.pricing`   债券定价、YTM、即期/远期
- :mod:`fi.curve`     利率期限结构 bootstrap 与插值
- :mod:`fi.risk`      久期、凸性、DV01、关键利率久期
- :mod:`fi.repo`      回购现金流、资金成本、杠杆与套息
- :mod:`fi.credit`    信用风险（Merton/KMV、约化模型）
- :mod:`fi.backtest`  债券策略回测框架
- :mod:`fi.plotting`  统一中文绘图样式
"""

__version__ = "0.1.0"

__all__ = [
    "data",
    "cashflow",
    "pricing",
    "curve",
    "risk",
    "repo",
    "credit",
    "backtest",
    "plotting",
]
