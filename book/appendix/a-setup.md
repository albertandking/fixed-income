# 附录A　本地环境配置（uv + QuantLib）

本附录说明如何在个人电脑上搭建与本书一致的 Python 计算环境，使正文中的每个数字都能由配套 notebook 复现。全书使用 **uv** 管理 Python 解释器与依赖，复用包 `fi` 与 QuantLib、akshare 等第三方库一并安装。只想在浏览器中运行代码的读者，可直接使用各章顶部的 Binder 徽章（见 A.5.2），无须在本地安装任何软件。

!!! abstract "本附录要点"
    1. 安装 uv（一条命令）；
    2. 获取本书仓库，执行 `uv sync --extra all` 装齐全部依赖；
    3. 用 `uv run pytest -q` 等命令验证安装，生成内置离线样本；
    4. 用 `uv run jupyter lab` 打开各章 notebook，或通过 Binder 在线运行；
    5. 遇到 QuantLib 安装、中文字体、国内网络、Windows 编码等问题时，查阅 A.7。

!!! note "关于版本号"
    本附录中出现的版本号均为作者在本机（Windows 11，2026年10月）实际运行得到的结果，仅作示例。各依赖的精确版本以仓库中的 `uv.lock` 为准；同步环境后可用 `uv tree --depth 1` 查看实际安装的版本。

---

## A.1 为什么使用 uv

### A.1.1 uv 是什么

uv 是由 Astral 公司开发的 Python 包与项目管理工具，用 Rust 编写。它把以往需要多种工具分别完成的工作集中到一条命令行中：下载并管理 Python 解释器（相当于 pyenv）、创建虚拟环境（相当于 venv）、解析与安装依赖（相当于 pip 与 pip-tools），并生成跨平台的锁文件。依赖解析与安装速度明显快于 pip，这在需要反复重建环境的课程教学中尤为便利。

### A.1.2 与 pip、conda 的差别

| 工具 | 管理对象 | 环境与锁定方式 | 在本书中的定位 |
| --- | --- | --- | --- |
| **pip** | Python 包（来自 PyPI） | 需另用 `venv` 建环境；`requirements.txt` 通常只记录直接依赖，间接依赖的版本不固定 | Binder 在线环境使用 |
| **conda** | Python 包及非 Python 二进制库（来自 conda 渠道） | 自带环境管理；锁定需借助额外工具 | 不使用；本书全部依赖均有 PyPI 预编译包，无须 conda |
| **uv** | Python 解释器与 Python 包 | 每个项目一个 `.venv`；`uv.lock` 记录全部直接与间接依赖的精确版本和校验哈希 | 本地环境的标准做法 |

conda 的优势在于能安装 C/Fortran 等非 Python 库，适合依赖复杂科学计算栈的场景。本书用到的 NumPy、SciPy、QuantLib 等在 PyPI 上均提供主流平台的预编译轮子（wheel），因此 uv 已能满足需要。两类工具不宜混用，否则容易造成"包装在哪个环境"的混乱；已安装 conda 的读者，在使用本书仓库前可先执行 `conda deactivate` 退出 conda 环境。

### A.1.3 锁文件与可复现性

仓库根目录下与环境有关的文件有三个：

- `pyproject.toml`：声明项目元数据、核心依赖与可选依赖组（extras），以及 Python 版本下限 `requires-python = ">=3.11"`；
- `.python-version`：内容为 `3.14`，uv 据此选择（必要时自动下载）Python 3.14 解释器；
- `uv.lock`：由 uv 自动生成的锁文件，记录全部依赖（含间接依赖）的精确版本、下载地址与哈希值，并按操作系统分别给出解析结果（文件中的 `resolution-markers` 一项即为平台标记）。

教材的数值结果依赖于库的具体版本，例如 QuantLib 的日历与日计数实现、pandas 的默认行为都可能随版本变化。`uv.lock` 入库后，读者在各自的平台上执行 `uv sync`，安装的都是锁文件中指定的版本，这是"正文每个数字都能被 notebook 复现"的基础。`pyproject.toml` 中的 `[tool.uv] package = true` 表示把本仓库本身作为一个包安装进 `.venv`：uv 以可编辑（editable）方式安装 `src/fi/`，因此在仓库内任何目录下都可以直接 `import fi`，修改 `src/fi/` 中的代码后也无须重新安装。

---

## A.2 安装 uv

以下命令摘自 uv 官方文档（<https://docs.astral.sh/uv/getting-started/installation/>，2026年10月核对）。安装程序会把 `uv` 放到用户目录下并写入 `PATH`，安装后需重新打开终端。

**macOS 与 Linux**（终端中执行）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# 系统没有 curl 时可改用 wget：
wget -qO- https://astral.sh/uv/install.sh | sh
```

**Windows**（在 PowerShell 中执行）：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

其中 `-ExecutionPolicy ByPass` 用于允许运行从网络下载的安装脚本。官方文档同时列出了其他安装方式：macOS 可用 `brew install uv`，Windows 可用 `winget install --id=astral-sh.uv -e` 或 `scoop install main/uv`，已有 Python 环境时也可用 `pipx install uv` 或 `pip install uv`。

安装完成后，在新终端中确认版本：

```bash
uv --version          # 作者本机输出：uv 0.12.3 (... x86_64-pc-windows-msvc)
```

以后升级 uv 只需执行 `uv self update`（仅适用于通过官方安装脚本安装的 uv；用 Homebrew、winget 等安装的，用对应的包管理器升级）。

!!! tip "不必预先安装 Python"
    uv 会根据 `.python-version` 自动下载所需版本的 Python，并与系统中已有的 Python 互不干扰。已安装其他版本 Python 的读者无须卸载，也无须修改系统 `PATH`。

---

## A.3 获取本书仓库并同步环境

### A.3.1 克隆仓库

本书仓库托管在 GitHub。已安装 Git 的读者执行：

```bash
git clone https://github.com/albertandking/fixed-income.git
cd fixed-income
```

未安装 Git 时，也可在仓库主页 <https://github.com/albertandking/fixed-income> 点击 "Code → Download ZIP" 下载压缩包并解压，效果相同，只是之后不能用 `git pull` 获取更新。

### A.3.2 一条命令同步环境

在仓库根目录执行：

```bash
uv sync --extra all
```

该命令依次完成以下工作：读取 `.python-version`，找到或下载 Python 3.14；在仓库根目录创建 `.venv` 虚拟环境；按 `uv.lock` 安装核心依赖与全部可选依赖；以可编辑方式安装复用包 `fi`。首次同步需要下载约一百五十个包，耗时取决于网速；此后再次执行只做增量检查，通常在一秒以内完成。

### A.3.3 可选依赖组（extras）

`pyproject.toml` 把依赖分为核心依赖与若干可选组。核心依赖为 `numpy`、`pandas`、`scipy`、`matplotlib`，任何同步方式都会安装。可选组如下：

| extra | 包含的包 | 用途 |
| --- | --- | --- |
| `data` | `akshare`、`tushare` | 联网抓取中国市场数据（附录C） |
| `quantlib` | `QuantLib` | 与 `fi` 对拍的定价库，含权债与衍生品章节使用 |
| `book` | `mkdocs-material`、`mkdocs-print-site-plugin`、`jupyter`、`nbconvert` | 运行 notebook、本地预览成书 |
| `docx` | `python-docx` | 导出 Word 版教材（另需系统安装 pandoc，见 A.6.2） |
| `all` | 以上四组，外加 `pytest` | 一键装齐，推荐 |

也可以只安装需要的组，多个组可以叠加：

```bash
uv sync                                  # 仅核心依赖
uv sync --extra quantlib --extra book    # QuantLib + Jupyter
```

!!! warning "uv sync 默认为精确同步"
    `uv sync` 会使 `.venv` 与所选依赖组**完全一致**，不在所选组中的包会被卸载。例如，已执行 `uv sync --extra all` 后再执行 `uv sync --extra book`，akshare、QuantLib 等二十余个包会被移除。需要保留已装的包时，加上 `--inexact` 选项，或者始终使用 `uv sync --extra all`。执行前可加 `--dry-run` 查看将要发生的变化。

### A.3.4 使用环境：uv run

同步完成后，不必手动"激活"虚拟环境，只需在命令前加 `uv run`，uv 会在 `.venv` 中执行该命令，并在执行前自动检查环境是否与锁文件一致：

```bash
uv run python my_script.py
uv run python -c "import sys; print(sys.executable)"   # 输出应指向仓库内的 .venv
```

习惯激活环境的读者也可以手动激活：macOS/Linux 执行 `source .venv/bin/activate`，Windows PowerShell 执行 `.venv\Scripts\activate`，Git Bash 执行 `source .venv/Scripts/activate`。

---

## A.4 验证安装

### A.4.1 冒烟测试

```bash
uv run pytest -q
```

测试文件 `tests/` 检查复用包 `fi` 及其各子模块能否导入、内置样本能否读取，以及部分核心数值函数（应计利息、到期收益率求解等）的结果。全部通过时输出形如 `30 passed in 1.59s`（测试数量随仓库更新可能变化）。

### A.4.2 检查 fi 与 QuantLib

```bash
uv run python -c "import fi, QuantLib as ql; print(fi.__version__, ql.__version__)"
```

作者本机输出 `0.1.0 1.42.1`。若提示 `ModuleNotFoundError: No module named 'QuantLib'`，说明同步时未包含 `quantlib` 组，执行 `uv sync --extra all` 即可。

进一步确认 QuantLib 可以正常定价，可以运行第3章使用的对拍代码：用 `fi.pricing.price_bond` 与 QuantLib `FixedRateBond` 分别为一只 3 年期、票面利率 3%、年付息的债券定价。

```python
import QuantLib as ql
from fi.cashflow import make_cashflows
from fi.pricing import price_bond

cfs, ts = make_cashflows(coupon_rate=0.03, maturity=3, freq=1, face=100)

today = ql.Date(15, 6, 2026)
ql.Settings.instance().evaluationDate = today
sched = ql.Schedule(today, today + ql.Period(3, ql.Years), ql.Period(ql.Annual),
                    ql.China(ql.China.IB), ql.Following, ql.Following,
                    ql.DateGeneration.Backward, False)
dc = ql.ActualActual(ql.ActualActual.ISDA)
bond = ql.FixedRateBond(0, 100.0, sched, [0.03], dc)

for y in (0.02, 0.03, 0.04):
    p_fi = price_bond(cfs, ts, y, 1)
    p_ql = ql.BondFunctions.cleanPrice(bond, ql.InterestRate(y, dc, ql.Compounded, ql.Annual))
    print(f"y={y:.0%}  fi={p_fi:.4f}  QuantLib={p_ql:.4f}")
```

本机输出三行，两种方法在 2%、3%、4% 三个收益率下分别得到约 102.88、100.00、97.22，二者在四位小数上一致。

### A.4.3 生成内置离线样本

```bash
uv run python scripts/make_sample_data.py
```

脚本在 `data/processed/` 下写出两份内置样本：`cgb_yield_curve.csv`（9 行）与 `money_market.csv`（250 行），字段含义见附录C 的 C.1 节。这两份文件已随仓库提供，重新生成的结果与入库版本相同；只有在文件被误删或修改后，才需要重新运行。`fi.data.load_sample()` 找不到样本时，会提示执行这条命令。

---

## A.5 运行 notebook

### A.5.1 本地运行：JupyterLab

```bash
uv run jupyter lab
```

命令会启动 JupyterLab 并在浏览器中打开（作者本机为 JupyterLab 4.5.8）。由于 JupyterLab 本身就安装在 `.venv` 中，其默认内核即为该环境的 Python，无须另行注册内核。在左侧文件栏进入 `notebooks/`，即可打开各章 notebook（如 `ch01_fi_overview.ipynb`）；习题解答位于 `notebooks/solutions/`。使用 VS Code 的读者，可在打开 notebook 后把内核选为仓库下 `.venv` 中的 Python。

需要以批处理方式检查某章 notebook 能否完整运行时，可执行：

```bash
uv run jupyter nbconvert --to notebook --execute notebooks/ch01_fi_overview.ipynb --output-dir /tmp/nbcheck
```

`--output-dir` 把执行结果写到别处，以免覆盖仓库中的 notebook；若确需更新仓库中的输出，可改用 `--inplace`。

### A.5.2 在线运行：Binder

每章正文顶部的 Binder 徽章可在 mybinder.org 上打开该章 notebook。Binder 按仓库中的 `binder/requirements.txt` 构建环境：以 pip 安装本书复用包及 `data`、`quantlib` 两个依赖组，并安装 JupyterLab。首次构建需要数分钟，会话闲置一段时间后会被回收，修改不会保存。

Binder 使用 pip 而非 uv 安装依赖，不读取 `uv.lock`，所装版本可能与本地不同，个别数值的末位可能因此出现差异。正文数字以本地 `uv sync` 环境的运行结果为准。

### A.5.3 环境检查单元

每个 notebook 的第一个代码单元检查复用包 `fi` 是否可用：

```python
import importlib.util
if importlib.util.find_spec('fi') is None:
    raise ModuleNotFoundError('未找到复用包 fi：请在仓库根目录执行 `uv sync`，再用 `uv run jupyter lab` 启动（见附录A）。')
```

本地已执行 `uv sync` 或在 Binder 中运行时，`fi` 已经安装，该单元不做任何事；否则立即报错并提示安装方法，以免在后续单元中出现难以定位的导入错误。

---

## A.6 本地预览与导出

### A.6.1 本地预览网页版

```bash
uv run mkdocs serve
```

MkDocs 会构建全书并启动本地服务器。由于 `mkdocs.yml` 中的 `site_url` 带有 `/fixed-income/` 路径，预览地址为 <http://127.0.0.1:8000/fixed-income/>（访问 `http://127.0.0.1:8000/` 会自动跳转）。修改 `book/` 下的 Markdown 或 `mkdocs.yml` 后，页面会自动刷新。按 `Ctrl+C` 停止服务器。

提交修改前，应执行与持续集成（CI）相同的严格构建，断链或引用错误会使构建失败：

```bash
uv run mkdocs build --strict
```

仓库的 `.github/workflows/deploy.yml` 在每次推送到 `main` 分支后，依次执行 `uv sync --extra book`、`uv run python scripts/make_sample_data.py`、`uv run mkdocs build --strict`，再把生成的网站发布到 GitHub Pages。

### A.6.2 导出 Word 版

```bash
uv run python scripts/make_docx.py
```

脚本按 `mkdocs.yml` 的 `nav` 顺序，把正文导出为 `dist/固定收益证券-全书.docx` 和 `dist/chapters/` 下的分章文件；`dist/` 不入库。加 `--book-only` 只生成全书文件，加 `--chapters-only` 只生成分章文件。

该脚本需要 `docx` 依赖组（`uv sync --extra all` 已包含），并调用系统中的 **pandoc**（要求版本不低于 3.8，作者本机为 3.12.1）。pandoc 不是 Python 包，需单独安装，安装方法见 <https://pandoc.org/installing.html>：Windows 可执行 `winget install --source winget --exact --id JohnMacFarlane.Pandoc`，macOS 可执行 `brew install pandoc`。安装后用 `pandoc --version` 确认。

---

## A.7 常见问题

### A.7.1 QuantLib 安装失败或需要编译

QuantLib 的 Python 包在 PyPI 上提供了 Windows、macOS（Intel 与 Apple Silicon）、Linux（x86_64 与 aarch64）的预编译轮子。以 `uv.lock` 中锁定的 QuantLib 1.42.1 为例，其通用轮子带有 `cp38-abi3` 标记，可用于 CPython 3.8 及以后的各个版本，因此在上述平台上安装时不需要编译。

如果安装过程开始从源码构建（输出中出现编译 C++ 的信息并长时间停留），通常意味着当前平台或解释器没有匹配的轮子，例如使用了较少见的处理器架构或操作系统。此时应首先确认使用的是 uv 管理的 CPython（`uv run python -c "import sys; print(sys.version)"`），而不是自行编译 QuantLib；从源码编译 QuantLib 需要 C++ 编译器、Boost 库与较长时间，不适合课程环境。

### A.7.2 图中中文显示为方块

matplotlib 默认字体不含中文字形，直接绘图时中文会显示为方块，负号也可能显示异常。本书统一调用 `fi.plotting.use_chinese_style()`（`fi.plotting.new_axes()` 内部也会调用）：它把 `font.sans-serif` 设为按顺序尝试的中文字体列表 `Microsoft YaHei`、`SimHei`、`Noto Sans CJK SC`、`PingFang SC`、`Arial Unicode MS`，并设置 `axes.unicode_minus = False` 以正确显示负号。

Windows 与 macOS 一般自带列表中的字体。若仍显示方块，可用下面的代码检查本机有哪些候选字体可用：

```python
from matplotlib import font_manager as fm

available = {f.name for f in fm.fontManager.ttflist}
for name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "PingFang SC", "Arial Unicode MS"]:
    print(f"{name:<18}", "可用" if name in available else "未找到")
```

作者本机（Windows）的结果为 Microsoft YaHei 与 SimHei 可用。若全部"未找到"，需要先安装中文字体。Linux 中常用的做法是安装 Noto CJK 字体，例如在 Debian/Ubuntu 系统中执行 `sudo apt-get install fonts-noto-cjk`，然后删除 matplotlib 的字体缓存目录（其位置可用 `matplotlib.get_cachedir()` 查看）并重启内核，使 matplotlib 重新扫描字体。也可以不安装到系统，而用 `fm.fontManager.addfont("字体文件路径")` 临时注册某个字体文件，再把 `font.sans-serif` 设为该字体名称。

### A.7.3 国内网络下的下载加速

本书仓库已在 `pyproject.toml` 中把默认索引固定为清华大学 TUNA 镜像：

```toml
[[tool.uv.index]]
name = "tuna"
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"
default = true
```

`uv.lock` 中所有包的下载地址也指向该镜像，因此读者执行 `uv sync` 时，Python 包均从清华镜像下载，无须另作配置。依据 uv 文档（Configuration files 一节），项目级配置与用户级配置合并时项目级优先，即使读者在本机 `uv.toml` 中配置了其他镜像，本仓库仍使用清华镜像，锁文件不会被改写。作者已用 `uv lock --check` 确认，锁文件与该配置一致。

只有两种情形会覆盖这一设置：一是设置环境变量 `UV_DEFAULT_INDEX`，二是用 `--config-file` 或 `UV_CONFIG_FILE` 指定配置文件（此时 uv 不再读取项目配置）。这两种情形下，`uv sync` 或 `uv run` 会按新索引重写 `uv.lock` 中的下载地址；作者实测，包版本不变，改变的只是地址。这类改动不应提交到仓库，可用 `git checkout -- uv.lock` 还原。注意，`--frozen` 选项虽能避免重写锁文件，但此时 uv 直接按锁文件中的地址（即清华镜像）下载，所设的其他镜像并不生效。

清华镜像暂时无法访问时，可临时改用其他镜像（2026年10月本机均可访问），同步完成后还原锁文件：

```bash
# macOS / Linux / Git Bash：只影响当前终端
export UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/
uv sync --extra all
git checkout -- uv.lock      # 还原锁文件中的下载地址
```

| 镜像 | 地址 |
| --- | --- |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |
| 中国科学技术大学 | `https://mirrors.ustc.edu.cn/pypi/simple/` |

旧变量 `UV_INDEX_URL` 在 uv 文档中已标注为弃用（deprecated），应改用 `UV_DEFAULT_INDEX`。

uv 首次运行时还会从 GitHub 下载 Python 解释器，这一步不受上述索引设置影响。下载较慢时，可在用户级配置文件 `uv.toml`（macOS/Linux 为 `~/.config/uv/uv.toml`，Windows 为 `%APPDATA%\uv\uv.toml`）中加入 `python-install-mirror`，例如南京大学镜像：

```toml
python-install-mirror = "https://mirrors.nju.edu.cn/github-release/astral-sh/python-build-standalone/"
```

### A.7.4 Windows 下的中文编码

简体中文版 Windows 的默认编码为 GBK（代码页 936）。作者在 Git Bash 中运行本书脚本时观察到两类现象：一是脚本打印的中文显示为乱码；二是用 `open()` 读取 UTF-8 文件（如 `.ipynb`）而未指定编码时，抛出 `UnicodeDecodeError: 'gbk' codec can't decode ...`。

解决办法是启用 Python 的 UTF-8 模式，使标准输出和 `open()` 的默认编码都变为 UTF-8：

```bash
# Git Bash：仅对当前终端有效
export PYTHONUTF8=1
uv run python scripts/make_sample_data.py
```

```powershell
# PowerShell：当前终端有效；改用 setx PYTHONUTF8 1 可长期生效（需重新打开终端）
$env:PYTHONUTF8 = 1
```

也可以对单条命令使用 `uv run python -X utf8 ...`。在自己编写的代码中，读写文本文件时显式写明 `encoding="utf-8"` 是更稳妥的习惯。

### A.7.5 其他问题

- **`uv` 命令找不到**：安装后未重新打开终端，`PATH` 尚未生效。关闭并重新打开终端即可。
- **`fi.data.load_sample` 报 `FileNotFoundError`**：内置样本缺失，执行 `uv run python scripts/make_sample_data.py`（A.4.3）。
- **联网接口报错**：akshare、tushare 的接口依赖第三方网站，可能因网站改版、访问频率限制或网络代理而失败。处理方法见附录C；本书所有 notebook 默认只使用内置离线样本，断网时也能运行。
