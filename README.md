# 固定收益证券：理论、模型与中国市场实践（Python 编程）

面向中国高年级本科生（可本研贯通）的固定收益证券教材。

- 正文用 Markdown 编写（`book/` 目录）
- 代码放在 Jupyter Notebook 中（`notebooks/` 目录），可本地逐格运行
- 每章习题的**编程实验完整可运行解答**放在 `notebooks/solutions/`（每章一个，离线可执行；各章正文"习题参考答案与详解"含 Colab 链接）
- 正文按需引用 / 嵌入 notebook 的代码与输出（通过 `scripts/export_notebooks.py` 手动导出）
- 数据：内置示例数据集（离线可跑）+ 中国市场接口（akshare / tushare，联网抓取）
- 环境：uv 管理，推荐 Python 3.14（兼容 3.11+）；成书：MkDocs + Material 主题
- 复现：`uv.lock` 锁定全部依赖精确版本

> 工程结构与写作约定见 [`仓库结构与命名规范.md`](仓库结构与命名规范.md)；完整目录见 [`大纲-v2.md`](大纲-v2.md)。

## 在线访问

- 📖 在线阅读（GitHub Pages）：https://albertandking.github.io/fixed-income/
- ▶️ 在线运行代码：每章正文顶部都有 Colab 与 Binder 徽章，点开即可在云端运行该章 notebook。

## 目录（8 部分 / 18 章）

| 部分 | 章 |
|---|---|
| 一·基础与工具 | 1 概述　2 计息惯例与货币时间价值 |
| 二·定价与收益率 | 3 债券定价　4 收益率计量　5 利率期限结构 |
| 三·风险度量与组合 | 6 久期与凸性　7 组合管理 |
| 四·市场机制 | 8 货币市场工具与回购市场 |
| 五·含权与高级品种 | 9 浮息债　10 含权债　11 可转债 |
| 六·信用与结构化 | 12 信用风险　13 结构化产品/ABS |
| 七·利率衍生品 | 14 期货与远期　15 利率互换　16 利率期权 |
| 八·综合应用 | 17 投资策略与回测　18 风险管理系统 |

## 快速开始

```bash
# 1. 安装环境（uv 会自动下载 Python 3.14，已验证兼容 QuantLib 1.42）
uv sync --extra all          # 一键装齐全部（data + quantlib + opt + book + pytest）
# 或按需分别安装：
#   uv sync                  # 仅核心依赖
#   uv sync --extra data     # 联网抓取中国市场数据（akshare/tushare）
#   uv sync --extra quantlib # 衍生品/含权债定价（QuantLib）
#   uv sync --extra book     # 成书工具链（MkDocs/Jupyter）

# 2. 生成内置示例数据（一次，离线）
uv run python scripts/make_sample_data.py

# 3. 运行书中代码
uv run jupyter lab

# 4. 本地预览整本书
uv run python scripts/export_notebooks.py
uv run mkdocs serve          # 浏览器打开 http://127.0.0.1:8000
```

## 写作约定

- 一章 = 一个 `book/partX/NN-题目.md` + 一个 `notebooks/chNN_主题.ipynb`
- 复用逻辑（计息、定价、曲线、风险、信用、回测、绘图）抽进 `src/fi/`，正文与 notebook 都 `from fi import ...`
- 每章统一结构：学习目标 → 推导 → 例题 → 中国市场案例 → 习题与编程实验 → 本章小结

## 许可

- 代码（`src/`、`scripts/`、`notebooks/`）：MIT
- 正文与图表（`book/`）：CC BY 4.0
