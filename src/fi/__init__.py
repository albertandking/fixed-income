"""fi —— 《固定收益证券》全书复用工具包。

正文与各章 notebook 统一通过 ``from fi import ...`` 调用复用逻辑，
避免代码在正文与 notebook 两处维护。各子模块：

- :mod:`fi.data`      数据读取 / 内置离线样本加载
- :mod:`fi.cashflow`  现金流、计息惯例、应计利息
- :mod:`fi.pricing`   债券定价、YTM、即期/远期
- :mod:`fi.curve`     利率期限结构 bootstrap 与插值
- :mod:`fi.risk`      久期、凸性、DV01、关键利率久期
- :mod:`fi.repo`      回购现金流、资金成本、杠杆与套息
- :mod:`fi.portfolio` 组合久期、久期匹配（免疫）、现金流匹配
- :mod:`fi.frn`       浮动利率债券定价、折现利差
- :mod:`fi.tree`      利率二叉树与含权债定价
- :mod:`fi.convertible` 可转换债券定价（股票二叉树）
- :mod:`fi.credit`    信用风险（Merton/KMV、约化模型）
- :mod:`fi.securitization` ABS/MBS 分层、损失分配与现金流瀑布
- :mod:`fi.futures`   国债期货：转换因子、CTD、套保比率、FRA
- :mod:`fi.swap`      利率互换：平价互换利率、估值、DV01、互换曲线 bootstrap
- :mod:`fi.rateopt`   利率期权：Cap/Floor/Swaption 的 Black 定价与隐含波动率
- :mod:`fi.var`       风险价值 VaR/CVaR（历史/参数/蒙特卡洛）、压力与情景
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
    "portfolio",
    "frn",
    "tree",
    "convertible",
    "credit",
    "securitization",
    "futures",
    "swap",
    "rateopt",
    "var",
    "backtest",
    "plotting",
]
