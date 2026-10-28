# 附录A　本地环境配置（uv + QuantLib）

本附录说明如何在个人电脑上搭建与本书一致的 Python 计算环境，使正文中的每个数字都能由配套 notebook 复现。全书使用 **uv** 管理 Python 解释器与依赖，复用包 `fi` 与 QuantLib、akshare 等第三方库一并安装。只想在浏览器中运行代码的读者，可直接使用各章顶部的 Colab/Binder 徽章（见 A.5.2），无须在本地安装任何软件。

!!! abstract "本附录要点"
    1. 安装 uv（一条命令）；
    2. 获取本书仓库，执行 `uv sync --extra all` 装齐全部依赖；
    3. 用 `uv run pytest -q` 等命令验证安装，生成内置离线样本；
    4. 用 `uv run jupyter lab` 打开各章 notebook，或在 Colab/Binder 上在线运行；
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
| **pip** | Python 包（来自 PyPI） | 需另用 `venv` 建环境；`requirements.txt` 通常只记录直接依赖，间接依赖的版本不固定 | Colab 与 Binder 在线环境使用 |
| **conda** | Python 包及非 Python 二进制库（来自 conda 渠道） | 自带环境管理；锁定需借助额外工具 | 不使用；本书全部依赖均有 PyPI 预编译包，无须 conda |
| **uv** | Python 解释器与 Python 包 | 每个项目一个 `.venv`；`uv.lock` 记录全部直接与间接依赖的精确版本和校验哈希 | 本地环境的标准做法 |

conda 的优势在于能安装 C/Fortran 等非 Python 库，适合依赖复杂科学计算栈的场景。本书用到的 NumPy、SciPy、QuantLib、cvxpy 等在 PyPI 上均提供主流平台的预编译轮子（wheel），因此 uv 已能满足需要。两类工具不宜混用，否则容易造成"包装在哪个环境"的混乱；已安装 conda 的读者，在使用本书仓库前可先执行 `conda deactivate` 退出 conda 环境。

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
| `opt` | `cvxpy` | 凸优化求解，用于组合优化（`pyproject.toml` 所注用途） |
| `book` | `mkdocs-material`、`mkdocs-print-site-plugin`、`jupyter`、`nbconvert` | 运行 notebook、本地预览成书 |
| `docx` | `python-docx` | 导出 Word 版教材（另需系统安装 pandoc，见 A.6.2） |
| `all` | 以上五组，外加 `pytest` | 一键装齐，推荐 |

也可以只安装需要的组，多个组可以叠加：

```bash
uv sync                                  # 仅核心依赖
uv sync --extra quantlib --extra book    # QuantLib + Jupyter
```

!!! warning "uv sync 默认为精确同步"
    `uv sync` 会使 `.venv` 与所选依赖组**完全一致**，不在所选组中的包会被卸载。例如，已执行 `uv sync --extra all` 后再执行 `uv sync --extra book`，akshare、QuantLib、cvxpy 等约三十个包会被移除。需要保留已装的包时，加上 `--inexact` 选项，或者始终使用 `uv sync --extra all`。执行前可加 `--dry-run` 查看将要发生的变化。

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

### A.5.2 在线运行：Colab 与 Binder

每章正文顶部都有两个徽章：

- **Colab**：在 Google Colab 中打开该章 notebook，使用 Google 提供的云端 Python 环境；
- **Binder**：在 mybinder.org 上按仓库中的 `binder/requirements.txt` 构建环境。该文件以 pip 安装本书复用包及 `data`、`quantlib`、`opt` 三个依赖组，并安装 JupyterLab。Binder 首次构建需要数分钟，会话闲置一段时间后会被回收，修改不会保存。

两种在线环境都使用 pip 而非 uv 安装依赖，不读取 `uv.lock`，所装版本可能与本地不同，个别数值的末位可能因此出现差异。

### A.5.3 自举单元的作用

每个 notebook 的第一个代码单元是"自举单元"，内容如下：

```python
import importlib.util, sys, subprocess
if importlib.util.find_spec('fi') is None:
    if 'google.colab' in sys.modules:
        subprocess.run(['git', 'clone', '--depth', '1',
                        'https://github.com/albertandking/fixed-income.git', '/content/fi-book'], check=False)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '/content/fi-book'], check=False)
    else:
        print('提示：请在仓库根目录执行 `uv sync --extra all` 后再运行本 notebook。')
```

它首先检查当前环境能否找到 `fi`。本地已执行 `uv sync` 或在 Binder 中运行时，`fi` 已经安装，该单元不做任何事；在 Colab 中则把仓库浅克隆到 `/content/fi-book`，再用 pip 以可编辑方式安装；在其他未安装 `fi` 的环境中，只打印提示。

!!! warning "在 Colab 中使用自举单元的两点注意"
    1. 自举单元执行的是 `pip install -e /content/fi-book`，只安装核心依赖，不包括 QuantLib、akshare 等可选依赖。需要这些库的章节，可在 Colab 中另加一个单元执行 `%pip install QuantLib akshare`。
    2. 可编辑安装通过写入 `.pth` 文件生效，而 Python 只在启动时读取 `.pth` 文件。作者在本地模拟这一流程时发现，同一进程内安装完成后仍找不到 `fi`，新进程则可以正常导入。因此，若运行自举单元后紧接着出现 `ModuleNotFoundError: No module named 'fi'`，应在 Colab 菜单中重启会话（Runtime → Restart session），再从第一个单元起依次运行；此时 `fi` 已安装，自举单元会直接跳过。

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

作者本机（Windows）的结果为 Microsoft YaHei 与 SimHei 可用。若全部"未找到"，需要先安装中文字体。Linux（包括 Colab）中常用的做法是安装 Noto CJK 字体，例如在 Debian/Ubuntu 系统中执行 `sudo apt-get install fonts-noto-cjk`（Colab 中执行 `!apt-get install -y fonts-noto-cjk`），然后删除 matplotlib 的字体缓存目录（其位置可用 `matplotlib.get_cachedir()` 查看）并重启内核，使 matplotlib 重新扫描字体。也可以不安装到系统，而用 `fm.fontManager.addfont("字体文件路径")` 临时注册某个字体文件，再把 `font.sans-serif` 设为该字体名称。

### A.7.3 国内网络下的下载加速

uv 默认从 PyPI（`https://pypi.org/simple`）下载包，从 GitHub 下载 Python 解释器。在国内网络下下载较慢时，可以改用国内镜像。镜像**不是必需的**：网络通畅时无须任何配置；镜像与 PyPI 之间也可能有短暂的同步延迟。

根据 uv 文档（Package indexes 与 Environment variables 两节），替换默认索引有三种方式。

**方式一：环境变量 `UV_DEFAULT_INDEX`**（只影响当前终端，适合临时使用）：

```bash
# macOS / Linux / Git Bash
export UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
uv sync --extra all
```

```powershell
# Windows PowerShell
$env:UV_DEFAULT_INDEX = "https://mirrors.aliyun.com/pypi/simple/"
uv sync --extra all
```

旧变量 `UV_INDEX_URL` 在文档中已标注为弃用（deprecated），应改用 `UV_DEFAULT_INDEX`。

**方式二：用户级配置文件 `uv.toml`**（对本机所有项目长期有效，推荐）。文件位置为 macOS/Linux 的 `~/.config/uv/uv.toml`、Windows 的 `%APPDATA%\uv\uv.toml`，内容为：

```toml
[[index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

`default = true` 表示用该镜像取代 PyPI 作为默认索引。同一文件中还可以加入 `python-install-mirror = "..."`，为 uv 下载 Python 解释器指定镜像（对应环境变量 `UV_PYTHON_INSTALL_MIRROR`），例如作者本机使用的南京大学镜像 `https://mirrors.nju.edu.cn/github-release/astral-sh/python-build-standalone/`。

**方式三：项目级 `pyproject.toml`**，写法为 `[[tool.uv.index]]` 加 `url` 与 `default = true`。这会把镜像地址写进仓库、影响所有使用者，因此本书仓库不采用这种方式，读者也不应把这类修改提交到仓库。

常用镜像地址如下（2026年10月本机均可访问，并已用 `UV_DEFAULT_INDEX` 实际安装测试过清华与阿里云两个）：

| 镜像 | 地址 |
| --- | --- |
| 清华大学 TUNA | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |
| 中国科学技术大学 | `https://mirrors.ustc.edu.cn/pypi/simple/` |

!!! note "锁文件与镜像"
    `uv.lock` 记录了每个包的下载地址。本仓库的锁文件是在配置清华镜像的环境下生成的，其中的地址均指向清华镜像，因此未作任何配置的读者执行 `uv sync` 时，Python 包实际上已经从该镜像下载；作者已用 `uv lock --check --no-config`（不读取任何本机配置）确认，此时锁文件有效，不会被改写。

    若读者配置了其他索引（包括阿里云等镜像，或显式指定 PyPI），uv 会认为锁文件需要更新，在执行 `uv sync` 或 `uv run` 时自动重写 `uv.lock` 中的下载地址。作者实测，以阿里云镜像重新锁定后，159 个包的版本与原锁文件完全一致，改变的只是地址。这类改动不应提交到仓库，可用 `git checkout -- uv.lock` 还原；也可以在同步时加 `--frozen` 选项，直接按锁文件安装而不重新锁定。由此可见，对本仓库而言，镜像配置主要用于加快 Python 解释器的下载（`python-install-mirror`）以及读者自己的其他项目。

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
