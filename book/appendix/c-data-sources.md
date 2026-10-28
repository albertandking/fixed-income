# 附录C　中国债券市场数据源

正文各章的案例默认使用仓库内置的离线样本，以保证断网可运行、结果可复现。第1、4、5、6、16章的编程实验要求读者改用真实市场数据，如中国国债收益率曲线、DR007/R007/GC007 等回购利率。本附录说明这些数据从何处获取、如何用 Python 读取，以及使用时应注意的口径问题。

!!! abstract "本附录要点"
    1. 数据使用的优先级：内置离线样本 > akshare/tushare（免费联网）> Wind（仅在有机构授权时可选）；
    2. akshare 中经本机实测可用的债券、货币市场与国债期货接口，以及取数、作图、与内置样本对比的完整代码；
    3. tushare 的注册、token 管理与债券相关接口（仅文档核对，未实测）；
    4. WindPy 的基本用法（仅作说明）；
    5. 官方与公开数据源网址，以及数据口径方面的常见陷阱。

!!! warning "关于实测日期与接口变动"
    本附录中标注"实测"的接口，均于 **2026年10月28日** 在作者本机（Windows 11，Python 3.14.3，akshare 1.18.64）实际联网调用，所列列名、起始日期、行数均为当日结果。akshare 等开源库通过抓取第三方网站取数，网站改版、访问频率限制或网络环境变化都可能使接口失效、列名改变或返回范围缩小。使用前应先用 `print(df.head())`、`df.columns` 检查返回结果，不应假定与本附录完全一致。

---

## C.1 数据使用原则

### C.1.1 内置离线样本

内置样本存放在 `data/processed/`，随仓库提供，由 `scripts/make_sample_data.py` 生成（见附录A 的 A.4.3），通过 `fi.data.load_sample(name)` 读取。函数依次查找同名的 `.parquet` 与 `.csv` 文件，均不存在时提示先运行生成脚本。

| 样本名 | 行数 | 字段 | 含义 | 使用章节 |
| --- | --- | --- | --- | --- |
| `cgb_yield_curve` | 9 | `tenor` | 期限（年）：0.25、0.5、1、2、3、5、7、10、30 | 第1、4、5、6章 |
| | | `yield_pct` | 国债到期收益率，单位为百分数（如 2.55 表示 2.55%） | |
| `money_market` | 250 | `date` | 日期（2025-01-02 起的工作日，字符串） | 第16章 |
| | | `dr007` | 存款类机构 7 天质押式回购利率，% | |
| | | `r007` | 全市场 7 天质押式回购利率，% | |
| | | `ncd_1y` | 1 年期同业存单收益率，% | |
| | | `cgb_10y` | 10 年期国债收益率，% | |

```python
from fi import data

curve = data.load_sample("cgb_yield_curve")
mm = data.load_sample("money_market")
print(curve.T)
print(mm.head(3))
print(mm.shape)
```

!!! note "内置样本是教学示意数据"
    两份样本均由确定性公式合成：`cgb_yield_curve` 是一条固定的向上倾斜曲线，`money_market` 由正弦函数叠加生成，并非真实行情。它们只用于演示计算方法，不能据此判断市场水平或得出实证结论。需要讨论当前曲线形态、利差或流动性事件时，应按本附录的方法获取真实数据。

### C.1.2 联网数据的存放

联网抓取的数据应保存在 `data/raw/` 目录下。该目录已在 `.gitignore` 中排除，不会入库，原因有三：真实行情数据的再分发可能受数据提供方条款约束；数据随时间更新，入库后容易与 notebook 中的结果不一致；部分数据体量较大。仓库中的 `scripts/fetch_data.py` 是预留的统一抓取脚本，目前仅创建 `data/raw/` 目录并打印提示，具体抓取逻辑尚未实现；读者可参照 C.2 的代码自行补充。

联网代码在 notebook 中应放在明确标注"联网"的小节，并配有失败时退回内置样本的处理，使整本 notebook 在断网时仍能运行完毕。

---

## C.2 akshare：免费、无需注册

akshare 是一个开源的 Python 财经数据接口库，数据来自交易所、中国货币网、中国债券信息网及东方财富、新浪财经等公开网站，无须注册即可使用。本书通过 `uv sync --extra data`（或 `--extra all`）安装，版本以 `uv.lock` 为准。接口文档见 <https://akshare.akfamily.xyz/>；需要注意，在线文档对应的是 akshare 的最新版本，个别接口的参数可能与本书锁定的版本不同，以本地 `help(ak.接口名)` 的输出为准。

### C.2.1 本书主用接口：`bond_zh_us_rate`

第1、4、5、6章习题中"用 akshare 取真实国债收益率"，指的就是 `ak.bond_zh_us_rate()`。其实测特征如下：

- **数据来源**：东方财富数据中心"中美国债收益率"页面；
- **参数**：`start_date`，格式为 `"YYYYMMDD"`，默认 `"19901219"`；
- **返回列**：`日期`，`中国国债收益率2年`、`5年`、`10年`、`30年`，`中国国债收益率10年-2年`，`中国GDP年增率`，以及对应的六个美国列，共 13 列；
- **频率与单位**：日频；收益率单位为百分数；`日期` 列为 Python `datetime.date` 对象（pandas 中显示为 `object` 类型）；
- **起始日期**：中国国债四个期限的数据均从 **2002-01-04** 开始；此前的行只有美国数据；
- **缺失值**：返回的日期是中美两国交易日的并集，在美国交易而中国休市的日子，中国各列为 `NaN`；
- **与中债曲线的关系**：实测 2026-10-27 与 2026-10-28 两日的 5 年、10 年、30 年数值（如 10-27 为 1.3487%、1.6258%、2.0406%）与同日中债国债收益率曲线（C.2.2）的对应期限完全一致，可以推断该接口的中国国债数据取自中债曲线；2 年期因 C.2.2 接口不含该期限而未能核对。

下面取出 2020 年以来中国国债四个期限的收益率：

```python
import akshare as ak
import pandas as pd

raw = ak.bond_zh_us_rate(start_date="20200101")
cols = {"中国国债收益率2年": 2, "中国国债收益率5年": 5,
        "中国国债收益率10年": 10, "中国国债收益率30年": 30}
cgb = (raw[["日期", *cols]]
       .rename(columns=cols)
       .assign(日期=lambda d: pd.to_datetime(d["日期"]))
       .set_index("日期")
       .dropna(how="all"))          # 去掉只有美国数据的日期
print(cgb.tail())
print("期间：", cgb.index[0].date(), "至", cgb.index[-1].date(), "，共", len(cgb), "个交易日")
```

接着把最近一个交易日的真实曲线与内置样本画在同一张图上，并比较各期限的差异与 10 年−2 年期限利差。这正是第1章编程实验7的要求，也是第4、5、6章相应实验的第一步。

```python
import numpy as np
import matplotlib.pyplot as plt
from fi import plotting

latest = cgb.dropna().iloc[-1]            # 最近一个四个期限都有数据的交易日
latest_date = cgb.dropna().index[-1]
sample = data.load_sample("cgb_yield_curve")

fig, ax = plotting.new_axes()
ax.plot(latest.index, latest.values, marker="o", label=f"中国国债（{latest_date:%Y-%m-%d}，akshare）")
ax.plot(sample["tenor"], sample["yield_pct"], marker="s", linestyle="--", label="内置样本（示意）")
ax.set_xlabel("期限（年）")
ax.set_ylabel("到期收益率 (%)")
ax.set_title("真实国债收益率曲线与内置样本")
ax.legend()
plt.show()

comp = pd.DataFrame({"真实": latest,
                     "样本": np.interp(latest.index, sample["tenor"], sample["yield_pct"])})
comp["差(bp)"] = (comp["真实"] - comp["样本"]) * 100
print(comp.round(2))
print(f"10年-2年利差：真实 {(latest[10] - latest[2]) * 100:.1f}bp，样本 {(comp.loc[10, '样本'] - comp.loc[2, '样本']) * 100:.1f}bp")
```

实测当日（2026-10-28）的真实曲线各期限低于样本约 72～92bp，10 年−2 年利差为 40.1bp，而样本为 60bp。曲线形态会随市场变化，读者运行时得到的数字将与此不同。

### C.2.2 中债国债收益率曲线：`bond_china_yield`

`bond_zh_us_rate` 只有四个期限。需要更多期限时，可用 `ak.bond_china_yield()` 直接读取中国债券信息网（中央结算公司）发布的收益率曲线：

- **参数**：`start_date`、`end_date`，格式 `"YYYYMMDD"`；**两者间隔须小于一年**，实测 2024-01-01 至 2026-10-28 的请求返回空表，而不报错；
- **返回列**：`曲线名称`、`日期`、`3月`、`6月`、`1年`、`3年`、`5年`、`7年`、`10年`、`30年`，单位为百分数；
- **曲线种类**：实测返回三条曲线，即"中债国债收益率曲线""中债中短期票据收益率曲线(AAA)""中债商业银行普通债收益率曲线(AAA)"，需要按 `曲线名称` 筛选；
- **历史范围**：实测 2015 年的数据可以正常取得。

取较长历史时，按年分段调用再拼接：

```python
def chinabond_curve(start, end, name="中债国债收益率曲线"):
    """分段（每段不足一年）调用 ak.bond_china_yield，返回以日期为索引、期限（年）为列的收益率表（%）。"""
    tenor_map = {"3月": 0.25, "6月": 0.5, "1年": 1, "3年": 3,
                 "5年": 5, "7年": 7, "10年": 10, "30年": 30}
    pieces, s, end = [], pd.Timestamp(start), pd.Timestamp(end)
    while s <= end:
        e = min(s + pd.DateOffset(years=1) - pd.Timedelta(days=2), end)
        df = ak.bond_china_yield(start_date=s.strftime("%Y%m%d"), end_date=e.strftime("%Y%m%d"))
        pieces.append(df[df["曲线名称"] == name])
        s = e + pd.Timedelta(days=1)
    out = pd.concat(pieces).drop(columns="曲线名称").rename(columns=tenor_map)
    out["日期"] = pd.to_datetime(out["日期"])
    return out.drop_duplicates("日期").set_index("日期").sort_index()

cb = chinabond_curve("2024-11-01", "2026-10-28")
print(cb.shape)
print(cb.tail(3))
```

### C.2.3 到期、即期与远期曲线：`bond_china_close_return`

第4章编程实验8要求先确认所取数据属于即期曲线还是到期收益率曲线。`bond_zh_us_rate` 与 `bond_china_yield` 给出的都是**到期收益率**。中国货币网（全国银行间同业拆借中心）发布的"收盘收益率曲线"同时提供到期、即期与远期三条曲线，可用 `ak.bond_china_close_return()` 读取：

- **参数**：`symbol` 为曲线名称，可选值由 `ak.bond_china_close_return_map()` 列出，实测共 75 种，包括"国债""政策性金融债(国开)""同业存单(AAA)""地方政府债(AAA)"等；`period` 为期限间隔，可取 `"0.1"`、`"0.5"`、`"1"`；`start_date`、`end_date` 格式为 `"YYYYMMDD"`；
- **返回列**：`日期`、`期限`（年）、`到期收益率`、`即期收益率`、`远期收益率`，单位为百分数；
- **单次最多 50 行**：akshare 在请求中固定每页 50 条，`period="1"` 时一个交易日的国债曲线恰为 50 个期限（0.083 年至 46 年），因此查询多个日期时只会返回前 50 行，应**逐日调用**；
- **历史范围有限**：实测 2026-07-01 及以后的日期可以取得，2026-06-15 及更早的日期返回空结果，并在 akshare 内部引发 `KeyError: 'newDateValue'`；非交易日也会引发同样的错误。该接口适合取近期曲线，长历史应使用 C.2.2 的中债曲线。

下面的代码取最近一个有数据的交易日的国债收盘曲线，并用第5章的 `fi.curve.bootstrap` 把 1～30 年的到期收益率近似视为年付息的平价收益率，剥离出即期利率，与货币网发布的即期曲线对比：

```python
from fi.curve import bootstrap

def cfets_close_curve(symbol="国债", lookback=10):
    """自今日起向前逐个工作日尝试，返回最近一个有数据的交易日的收盘收益率曲线（期限间隔 1 年）。"""
    for d in pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=lookback)[::-1]:
        ds = d.strftime("%Y%m%d")
        try:
            df = ak.bond_china_close_return(symbol=symbol, period="1", start_date=ds, end_date=ds)
        except KeyError:            # 当日无数据（节假日、尚未发布或超出可查询范围）
            continue
        if not df.empty:
            return df
    raise RuntimeError("最近若干个工作日均未取得数据")

cm = cfets_close_curve("国债")
grid = cm[(cm["期限"] >= 1) & (cm["期限"] <= 30) & (cm["期限"] % 1 == 0)].set_index("期限")
zeros, _ = bootstrap(grid["到期收益率"].to_numpy() / 100)

cmp_spot = pd.DataFrame({
    "到期收益率": grid["到期收益率"],
    "即期(货币网)": grid["即期收益率"],
    "即期(fi bootstrap)": zeros * 100,
})
cmp_spot["差(bp)"] = (cmp_spot["即期(fi bootstrap)"] - cmp_spot["即期(货币网)"]) * 100
print("曲线日期：", cm["日期"].iloc[0])
print(cmp_spot.loc[[1, 2, 5, 10, 20, 30]].round(4))
```

实测（曲线日期 2026-10-28）两种即期利率在所列各期限上的差异均小于 0.01bp，即在四位小数上一致。这表明，至少在该日，货币网发布的即期曲线可以由其到期收益率曲线按"年付息平价债、整数年节点"的假设逐期剥离精确复现，第5章的 bootstrap 方法与发布方的口径相符。读者换用其他曲线或日期时，仍应先做同样的核对，不宜默认口径一致。同一张表也显示了到期收益率与即期利率在长端的差距：20 年期到期收益率为 2.0417%，即期利率为 2.1029%，相差约 6bp。直接拿到期收益率代替即期利率做折现或推算远期利率，会在长端产生可观察的误差（第4、5章）。

### C.2.4 货币市场利率：Shibor、回购定盘利率、GC007、LPR

第16章编程实验8需要 DR007、R007、GC007 与 10 年期国债收益率。实测可用的 akshare 接口如下：

| 接口 | 数据内容 | 来源 | 实测要点 |
| --- | --- | --- | --- |
| `rate_interbank(market="上海银行同业拆借市场", symbol="Shibor人民币", indicator="3月")` | 单一期限 Shibor | 东方财富 | 列为 `报告日`、`利率`、`涨跌`；自 2006-10-08 起；`indicator` 可取 `"隔夜"`、`"1周"`、`"2周"`、`"1月"`、`"3月"`、`"6月"`、`"9月"`、`"1年"` |
| `macro_china_shibor_all()` | 全部 8 个期限的 Shibor | 金十数据 | 列为 `日期`、`O/N-定价`、`O/N-涨跌幅` 至 `1Y-定价`、`1Y-涨跌幅`；除首行（2015-05-08）外自 2017-03-17 起连续 |
| `repo_rate_query(symbol="回购定盘利率")` | FR001、FR007、FR014 | 中国货币网 | 返回近三年（实测自 2023-10-30 起） |
| `repo_rate_query(symbol="银银间回购定盘利率")` | FDR001、FDR007、FDR014 | 中国货币网 | 返回近一年 |
| `repo_rate_hist(start_date, end_date)` | FR 与 FDR 六个品种 | 中国货币网 | 起止日期须在一个月内；实测 2015 年可取（当时 FDR 各列为空） |
| `bond_zh_hs_daily(symbol="sh204007")` | 上交所 7 天国债回购 GC007 日 K 线 | 新浪财经 | 列为 `date`、`open`、`high`、`low`、`close`、`volume`，利率单位为 %；自 2016-11-24 起；`sh204001` 为 GC001，`sz131810` 为深交所 R-001 |
| `macro_china_lpr()` | 1 年期与 5 年期以上 LPR | 东方财富 | 本书只用 `TRADE_DATE`、`LPR1Y`、`LPR5Y` 三列 |

!!! warning "akshare 中没有 DR007、R007 加权平均利率的直接接口"
    在 akshare 1.18.64 的源码中检索，没有提供中国货币网"货币市场行情"中 DR007、R007 加权平均利率历史数据的接口。可用的替代是回购定盘利率：据中国货币网"回购定盘利率"页面的编制方案，FR007 以银行间市场每个交易日上午 9:00～11:30 的七天回购（R007）全部成交利率为样本，取排序后的中位数；FDR007 的样本则限于存款类机构之间以利率债为质押的七天回购（DR007）。因此，FDR007、FR007 分别与 DR007、R007 的样本范围相同，但统计时段（上午）与统计量（中位数而非加权平均）不同，二者数值接近而不相等。完成第16章实验时，可用 FDR007、FR007 作为近似并在报告中注明；需要严格的 DR007、R007 时，应从中国货币网（C.5）下载，或使用 tushare、Wind 等数据源。同样，GC007 的新浪日 K 线收盘价是收盘时的成交利率，与上交所发布的加权平均利率也不是同一指标。

```python
shibor_3m = ak.rate_interbank(market="上海银行同业拆借市场", symbol="Shibor人民币", indicator="3月")
fr = ak.repo_rate_query(symbol="回购定盘利率")
fdr = ak.repo_rate_query(symbol="银银间回购定盘利率")
gc007 = ak.bond_zh_hs_daily(symbol="sh204007")
lpr = ak.macro_china_lpr()

print(shibor_3m.tail(3))
print(fr.tail(3))
print(fdr.tail(3))
print(gc007.tail(3))
print(lpr[["TRADE_DATE", "LPR1Y", "LPR5Y"]].dropna().tail(3))
```

把上述序列与 C.2.1 的 10 年期国债收益率按日期对齐，可以得到一张与内置 `money_market` 样本结构相近的真实数据表，用于第16章的复盘：

```python
def as_series(df, date_col, value_col, name):
    """把某一列转换为以 DatetimeIndex 为索引的 Series。"""
    return df.set_index(pd.to_datetime(df[date_col]))[value_col].rename(name)

real_mm = pd.concat([
    as_series(fdr, "date", "FDR007", "fdr007"),      # DR007 的近似
    as_series(fr, "date", "FR007", "fr007"),         # R007 的近似
    as_series(gc007, "date", "close", "gc007"),
    cgb[10].rename("cgb_10y"),
], axis=1, join="inner").sort_index()                # 只保留四个序列都有数据的日期

real_mm["fr_fdr_bp"] = (real_mm["fr007"] - real_mm["fdr007"]) * 100
print(real_mm.shape)
print(real_mm.describe().round(3))
print("FR007-FDR007 利差最大的 5 个交易日：")
print(real_mm.nlargest(5, "fr_fdr_bp")[["fdr007", "fr007", "gc007", "fr_fdr_bp"]])
```

实测得到 2025-10-28 至 2026-10-28 的 243 个交易日。FR007−FDR007 利差的中位数为 4bp，最大值出现在 2025年12月29日至31日的跨年时点（20～30bp），也有个别交易日 FR007 略低于 FDR007。内置样本中 R007 始终高于 DR007，且没有跨年的集中波动，这也说明合成样本只能演示方法，而不能代替真实数据。

### C.2.5 国债期货

第11章涉及的国债期货行情，可从中金所日统计数据或新浪财经主力连续合约取得：

| 接口 | 数据内容 | 实测要点 |
| --- | --- | --- |
| `get_futures_daily(start_date, end_date, market="CFFEX")` | 中金所全部合约日行情 | 列为 `symbol`、`date`、`open`、`high`、`low`、`close`、`volume`、`open_interest`、`turnover`、`settle`、`pre_settle`、`variety`；用 `variety` 筛选 `TS`（2 年）、`TF`（5 年）、`T`（10 年）、`TL`（30 年） |
| `futures_hist_daily_cffex(date)` | 中金所单日行情 | 返回列与上一接口相同 |
| `futures_main_sina(symbol="T0", start_date, end_date)` | 10 年期国债期货主力连续合约 | 列为 `日期`、`开盘价`、`最高价`、`最低价`、`收盘价`、`成交量`、`持仓量`、`动态结算价`；实测 `动态结算价` 全为 0，结算价应以中金所数据为准；`TS0`、`TF0`、`TL0` 依此类推 |

```python
fut = ak.get_futures_daily(start_date="20261027", end_date="20261027", market="CFFEX")
tbond = fut[fut["variety"].isin(["TS", "TF", "T", "TL"])]
print(tbond[["symbol", "close", "settle", "volume", "open_interest"]].to_string(index=False))

t_main = ak.futures_main_sina(symbol="T0", start_date="20260101", end_date="20261028")
print(t_main.tail(3))
```

主力连续合约由不同月份的合约拼接而成，换月处的价格跳跃并非真实的收益，计算收益率或回测时应注意。

### C.2.6 缓存到本地与离线降级

联网取数耗时且可能失败，较好的做法是取一次后保存到 `data/raw/`，之后优先读取本地文件；联网失败时退回内置样本：

```python
from pathlib import Path

RAW = data.processed_dir().parent / "raw"        # 仓库下的 data/raw（不入库）
RAW.mkdir(exist_ok=True)

def load_cgb(refresh=False):
    """读取中国国债 2/5/10/30 年收益率：优先本地缓存，其次联网，最后退回内置样本。"""
    path = RAW / "cgb_eastmoney.csv"
    if path.exists() and not refresh:
        return pd.read_csv(path, index_col=0, parse_dates=True).rename(columns=int)   # CSV 列名读回为字符串
    try:
        df = ak.bond_zh_us_rate(start_date="20200101")
    except Exception as e:                        # 网络或接口异常
        print("联网失败，改用内置样本：", type(e).__name__)
        s = data.load_sample("cgb_yield_curve").set_index("tenor")["yield_pct"]
        return s.loc[[2, 5, 10, 30]].to_frame("样本").T.rename(columns=int)
    out = (df.set_index(pd.to_datetime(df["日期"]))[list(cols)]
             .rename(columns=cols).dropna(how="all"))
    out.to_csv(path)
    return out

print(load_cgb().tail(2))
```

### C.2.7 实测未成功或未列入的接口

以下接口在实测日未能取得数据，正文未采用：

- `bond_buy_back_hist_em`、`bond_sh_buy_back_em`、`bond_sz_buy_back_em`（东方财富交易所回购行情）：连接被对方服务器中断，经系统代理与直连均失败；GC001、GC007 改用 C.2.4 的新浪接口；
- `macro_china_swap_rate`（FR007 利率互换曲线）：返回空数据并引发 `ValueError`；
- `futures_settle_cffex`（中金所结算参数）：返回空表。

此外，`bond_gb_zh_sina(symbol="中国10年期国债")` 可以取得新浪财经的国债收益率日 K 线，但实测只返回最近 1000 个交易日，且 2026-10-27 的收盘值为 1.662%，与同日中债曲线的 1.6258% 相差约 4bp，数据口径未见说明，本书不采用。

!!! tip "联网失败时的排查"
    1. 先在浏览器中打开接口对应的网页（源码 docstring 中有网址，可用 `help(ak.接口名)` 查看），确认网站本身可以访问；
    2. 开启了系统代理的电脑上，requests 会自动读取系统代理设置，部分国内网站可能因此连接失败，可在代理软件中把这些网站设为直连后重试；
    3. 短时间内大量请求可能被网站限制访问，循环取数时应在请求之间暂停（如 `time.sleep(1)`）；
    4. 升级 akshare 可能修复失效的接口，但会改变 `uv.lock`，需要同时确认其他章节的结果不受影响。

---

## C.3 tushare：注册后使用

tushare Pro（<https://tushare.pro/>）是另一个常用的中国金融数据平台，以统一的 API 提供股票、基金、期货、债券与宏观数据。与 akshare 不同，它需要注册账号并取得 **token**（接口凭证），各接口按用户**积分**开放：积分越高，可调用的接口越多、频次越高。积分可通过注册、完善个人资料、参与社区等方式获得；官网"高校服务"栏目另有面向学生和教师的积分说明。

!!! warning "未实测说明"
    作者没有可用于本书的 tushare token，本节接口名称、参数与积分要求均依据 tushare 官方文档（<https://tushare.pro/document/2>，2026年10月28日核对）整理，**未经实际调用**。tushare 版本以 `uv.lock` 为准（本机为 1.4.29）。

### C.3.1 token 的设置与保管

token 相当于账户密码，**不得写进代码，也不得提交到代码仓库**。推荐把它保存为环境变量，在代码中读取：

```bash
# macOS / Linux / Git Bash（写入 ~/.bashrc 等启动文件可长期生效）
export TUSHARE_TOKEN="在 tushare 个人主页复制的 token"
```

```powershell
# Windows：setx 写入用户环境变量，重新打开终端后生效
setx TUSHARE_TOKEN "在 tushare 个人主页复制的 token"
```

tushare 也提供 `ts.set_token("token")`：其源码显示，该函数把 token 以明文写入用户主目录下的 `tk.csv` 文件，此后 `ts.pro_api()` 不带参数即可读取。这个文件位于仓库之外，不会被提交，但仍应注意不要在共享电脑上使用。

### C.3.2 与债券相关的接口

以下接口均已在官方文档中核实存在：

| 接口 | 文档名称 | 主要参数 | 积分或权限要求（文档所述） |
| --- | --- | --- | --- |
| `yc_cb` | 国债收益率曲线 | `ts_code="1001.CB"`（中债国债收益率曲线），`curve_type`（`"0"` 到期、`"1"` 即期），`trade_date` 或 `start_date`/`end_date`，`curve_term` | 单独权限，需联系平台管理员开通 |
| `shibor` | Shibor 利率 | `date` 或 `start_date`/`end_date`；返回 `on`、`1w`、`2w`、`1m`、`3m`、`6m`、`9m`、`1y` | 120 积分 |
| `shibor_quote` | Shibor 报价数据 | 同上 | 120 积分 |
| `shibor_lpr` | LPR 贷款基础利率 | 同上；返回 `1y`、`5y` | 120 积分可调取，正式权限 5000 积分 |
| `repo_daily` | 债券回购日行情 | `ts_code` 或 `trade_date`；返回 `repo_maturity`（如 GC001、GC007、R-001）、`close`、`weight`（加权价）等，单位为 % | 2000 积分 |
| `fut_daily` | 期货日线行情 | `ts_code`（如 `T2612.CFX`）或 `trade_date` 加 `exchange="CFFEX"` | 2000 积分 |
| `fut_mapping` | 期货主力与连续合约映射 | `ts_code` | 2000 积分 |
| `cb_basic`、`cb_daily` | 可转债基础信息与行情 | `ts_code` 等 | 2000 积分 |

`yc_cb` 同时提供中债国债收益率曲线的到期与即期两种曲线，期限节点较密（文档示例从 0 年到 50 年），是 C.2.3 货币网接口之外取得即期曲线的另一途径；`repo_daily` 的 `weight` 列是交易所回购的加权平均利率，比 C.2.4 中新浪日 K 线的收盘利率更接近上交所公布的 GC007 指标。

### C.3.3 示例代码

下面的代码在未设置 `TUSHARE_TOKEN` 时只打印提示，不会报错；设置后依次调用三个接口。积分不足时，tushare 会返回权限不足的错误信息。

```python
import os
import tushare as ts

token = os.environ.get("TUSHARE_TOKEN")
if not token:
    print("未设置环境变量 TUSHARE_TOKEN，跳过 tushare 示例。")
else:
    pro = ts.pro_api(token)
    shibor = pro.shibor(start_date="20260101", end_date="20261028")
    repo = pro.repo_daily(trade_date="20261027")
    curve = pro.yc_cb(ts_code="1001.CB", curve_type="1", trade_date="20261027")   # 即期曲线
    print(shibor.head())
    print(repo[repo["repo_maturity"].isin(["GC001", "GC007"])])
    print(curve.head())
```

tushare 返回的日期为 `"YYYYMMDD"` 格式的字符串，与 akshare 数据合并前应先用 `pd.to_datetime` 转换。

---

## C.4 Wind（万得）：仅在有授权时可选

Wind 金融终端是国内金融机构普遍使用的商业数据库，债券数据覆盖面广、口径统一。但它需要付费授权，大多数学生无法使用，因此本书**不依赖 Wind**，所有案例均可用内置样本或 akshare/tushare 完成。所在学校或实习单位提供 Wind 终端的读者，可以通过其 Python 接口 WindPy 取数。

WindPy 随 Wind 终端安装，需在终端的插件修复工具中完成 Python 接口的配置，不能从 PyPI 安装，因此也不在本书的 `uv.lock` 中。常用函数有三个：`w.start()` 启动并连接终端；`w.wsd(代码, 字段, 起始日, 截止日, 选项)` 取单个或多个证券的日频序列；`w.edb(指标代码, 起始日, 截止日, 选项)` 取经济数据库（EDB）中的宏观与利率指标。返回对象的 `ErrorCode` 为 0 表示成功，`Times` 与 `Data` 分别为日期列表与数据列表。证券代码、字段名和指标代码应在终端的代码生成器中查询，此处不展开。

```python
try:
    from WindPy import w
except ImportError:
    w = None
    print("未检测到 WindPy（需安装 Wind 终端并配置 Python 接口），跳过 Wind 示例。")

if w is not None:
    w.start()
    res = w.edb("在代码生成器中查询的指标代码", "2026-01-01", "2026-10-28", "")
    if res.ErrorCode == 0:
        print(res.Times[:3], res.Data[0][:3])
```

!!! note "未实测说明"
    作者本机未安装 Wind 终端，以上代码仅验证了未安装时的降级分支，WindPy 函数的用法依据其公开的接口说明概述。

---

## C.5 官方与公开数据源

akshare 等工具最终取自以下官方或公开网站。核对数据口径、查阅编制方法、下载 akshare 未覆盖的指标时，应直接访问这些网站。以下网址均于 2026年10月28日在作者本机访问成功。

| 机构 | 网址 | 主要数据 |
| --- | --- | --- |
| 中国外汇交易中心暨全国银行间同业拆借中心（中国货币网） | <https://www.chinamoney.com.cn/chinese/> | 银行间市场行情与基准利率 |
| | [Shibor](https://www.chinamoney.com.cn/chinese/bkshibor/) | 各期限 Shibor 报价与历史数据 |
| | [回购定盘利率](https://www.chinamoney.com.cn/chinese/bkfrr/) | FR001/FR007/FR014、FDR001/FDR007/FDR014 及其编制方案 |
| | [货币市场行情](https://www.chinamoney.com.cn/chinese/mkdatapm/) | 同业拆借、质押式回购（含 DR、R 系列加权利率）、买断式回购 |
| | [收盘收益率曲线历史数据](https://www.chinamoney.com.cn/chinese/bkcurvclosedyhis/) | 国债等各类曲线的到期、即期、远期收益率 |
| 中央国债登记结算有限责任公司（中国债券信息网） | <https://www.chinabond.com.cn/> | 债券发行、托管、估值信息 |
| | [中债收益率曲线](https://yield.chinabond.com.cn/) | 中债国债、政策性金融债、信用债等收益率曲线 |
| 银行间市场清算所（上海清算所） | <https://www.shclearing.com.cn/> | 同业存单、短期融资券、中期票据等的登记托管结算信息 |
| 上海证券交易所 | <https://www.sse.com.cn/>；[上证债券信息网](https://bond.sse.com.cn/) | 交易所债券行情；[7 天期国债回购（204007，GC007）利率数据](https://bond.sse.com.cn/data/standard/repocurve/sevenrepo/) |
| 深圳证券交易所 | <https://www.szse.cn/> | 深交所债券与质押式回购（R-001 等）行情 |
| 中国金融期货交易所 | <http://www.cffex.com.cn/> | 国债期货合约规则、[日统计](http://www.cffex.com.cn/rtj/)数据；如 [10 年期国债期货](http://www.cffex.com.cn/10tf/)页面 |
| 中国人民银行 | <https://www.pbc.gov.cn/> | [公开市场业务交易公告](http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html)；调查统计司[统计数据](http://www.pbc.gov.cn/diaochatongjisi/116219/116319/index.html)；金融市场司[金融市场运行分析](https://www.pbc.gov.cn/jinrongshichangsi/147160/147173/index.html)（如每月"金融市场运行情况"） |

作者本机访问中金所网站时，`https://` 地址连接失败而 `http://` 地址可以访问，故表中使用后者。第16章"延伸阅读"中另列有 Shibor 实施准则等文件的链接，可配合本表使用。

---

## C.6 数据口径与常见陷阱

### C.6.1 到期收益率曲线与即期曲线

`bond_zh_us_rate`、`bond_china_yield` 以及内置样本 `cgb_yield_curve` 给出的都是**到期收益率**曲线。到期收益率是使某只债券全部现金流现值等于其价格的单一折现率，不能直接用来给其他现金流折现，也不能直接代入远期利率公式。要得到即期曲线，有两种途径：一是从到期（平价）收益率出发，按第5章的方法 bootstrap（如 `fi.curve.bootstrap`，见[第5章](../part2/05-term-structure.md)）；二是直接取用数据源发布的即期曲线，如 C.2.3 的中国货币网收盘曲线或 C.3 的 tushare `yc_cb`（`curve_type="1"`）。即使采用第二种途径，也应弄清发布方的复利口径与付息假设，再与自己的计算结果比较（参见[第4章](../part2/04-yield-measures.md)习题8的提示）。

### C.6.2 百分数单位

本附录涉及的数据源，收益率与利率一律以**百分数**表示，如 `1.6345` 表示 1.6345%。`fi` 的定价与曲线函数则以**小数**为输入，如 `fi.curve.bootstrap` 要求 0.016345。代入前须除以 100，算完后再乘以 100 换回百分数；利差与变动通常以基点（bp，1bp = 0.01%）表示，即两个百分数之差乘以 100。单位混用是初学者最常见的错误之一，计算出的价格或久期若偏离常理数个数量级，应首先检查这一点。

### C.6.3 缺失值、节假日与调休

- 中国债券市场在法定节假日休市，并存在周末调休安排，交易日历与美国不同。合并多国或多来源数据时，应明确采用哪一方的交易日历；
- 不应把节假日用前值填充后当作真实成交数据参与统计（第16章 16.8.1 已指出），否则会低估波动率、扭曲回购利率的跨节效应；
- `bond_zh_us_rate` 中美国交易日、中国休市的行，中国各列为 `NaN`；`pd.concat(..., join="inner")` 只保留各序列都有数据的日期，`dropna()` 则删除含任一缺失值的行，两者都会改变样本，应根据研究目的选择；
- 数据源当日的最后一行可能是盘中或尚未定稿的数值，严格的研究应只使用已收盘的数据。

### C.6.4 不必做复权，但要注意价格口径

股票数据需要做除权除息复权，而收益率、利率序列不涉及复权。债券价格数据则要区分**净价**与**全价**（第3章）：交易所债券行情通常以净价报价，付息日前后全价会出现跳跃，而净价不会。国债期货主力连续合约存在换月跳跃（C.2.5），也需另行处理。

### C.6.5 同一指标在不同来源间的差异

本附录的实测已给出几个例子：中国货币网收盘曲线与中债曲线的 10 年期国债到期收益率，2026-10-27 分别为 1.6271% 与 1.6258%，2026-10-28 分别为 1.6268% 与 1.6345%，相差约 0.1～0.8bp，两者的编制机构与方法不同；新浪财经的 10 年期国债收益率与中债相差约 4bp；FDR007 与 DR007、GC007 收盘利率与加权平均利率的统计方法也不同。同一项研究应尽量只用一个来源的数据；确需拼接时，应在重叠期检查差异，并在报告中注明各指标的来源与口径。

### C.6.6 频率对齐

日频的收益率与回购利率、月度的 LPR 与货币供应量、季度的 GDP 增速混合分析时，需要先统一频率。降频通常用月末值（`df.resample("ME").last()`）或月均值（`.mean()`）；升频则应把低频指标在其发布日之后才视为已知，不能用当月末才公布的数据去解释当月初的市场变动，否则会引入"前视偏差"（look-ahead bias），使回测结果失真。
