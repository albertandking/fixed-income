# 附录B　QuantLib 核心类与用法速查

!!! info "本附录的定位与运行环境"
    本附录汇总全书各章"QuantLib 实现"小节实际用到的类与函数，按"日期—计息—曲线—工具—引擎"的顺序组织，供编写或核对对拍代码时查阅。所列代码均在 QuantLib 1.42.1（Python 绑定）下逐段实际运行，注释中的数值为实测输出；每段代码各自导入 `QuantLib`、设置估值日，可单独运行。安装方法见附录A（`uv sync --extra quantlib`）。QuantLib 的接口随版本演进，若本机版本不同，应先用 `ql.__version__` 确认版本，并以实测结果为准。

本书正文统一以 `import QuantLib as ql` 导入。下文"第N章"指正文中对应的"QuantLib 实现"小节，与之对照的 `fi` 数值均取自相应章节。

---

## B.1 QuantLib 的设计思路

QuantLib 是一个以 C++ 编写的开源量化金融库，Python 用户使用的是通过 SWIG 自动生成的绑定（QuantLib-SWIG 项目，PyPI 包名 `QuantLib`）。Python 层的类名、方法名与 C++ 基本一一对应，计算全部在 C++ 内核中完成。理解以下几条设计主线，有助于读懂全书的对拍代码。

**（1）日期与日历是一等公民。** QuantLib 不直接使用"年数"描述现金流，而是先用 `Date`、`Period`、`Calendar`、`Schedule` 生成真实日期，再由计息惯例 `DayCounter` 把两个日期之间的区间折算为年化分数。教科书公式中的 $t=1,2,3$ 在 QuantLib 中对应的是具体日期，这正是多数对拍差异的根源（B.9）。

**（2）利率是"数值 + 计息惯例 + 复利方式 + 频率"。** `InterestRate` 与各类期限结构在报出利率时都必须指明 `DayCounter`、`Compounding`（`Simple`、`Compounded`、`Continuous`）与 `Frequency`。只给出"3%"而不说明口径，在 QuantLib 中无法构造出利率对象。

**（3）金融工具与定价引擎分离。** `Instrument`（如 `FixedRateBond`、`VanillaSwap`、`Cap`）只描述合约条款；`PricingEngine`（如 `DiscountingBondEngine`、`BlackCapFloorEngine`）决定用什么模型和市场数据定价。同一只债券可以先后挂上贴现引擎、树引擎，而无须重建合约对象。调用 `NPV()`、`cleanPrice()` 等方法时，工具把条款交给引擎计算并缓存结果。

**（4）Handle 与 Quote 的观察者机制。** 市场数据通常以 `SimpleQuote`（可变报价）包装，再经 `QuoteHandle`、`YieldTermStructureHandle` 等句柄传给曲线和引擎。句柄背后的对象发生变化时，依赖它的曲线、工具会收到通知并在下次取值时重新计算。这一"观察者（observer）"模式使情景分析只需修改报价，而不必重建整条计算链。

**（5）全局估值日。** `ql.Settings.instance().evaluationDate` 是全局的"今天"。未显式设置时，它取运行代码当天的系统日期，结果会随运行日期变化。本书所有对拍代码都在开头显式设置估值日。

下面的例子同时演示工具/引擎分离、观察者机制与估值日的作用：

```python
import QuantLib as ql

ql.Settings.instance().evaluationDate = ql.Date(15, 6, 2026)
dc = ql.Thirty360(ql.Thirty360.BondBasis)
q = ql.SimpleQuote(0.03)                                  # 可变的市场报价
curve = ql.YieldTermStructureHandle(                       # 参考日随估值日移动的平坦曲线
    ql.FlatForward(0, ql.NullCalendar(), ql.QuoteHandle(q), dc, ql.Compounded, ql.Annual))
sched = ql.Schedule(ql.Date(15, 6, 2026), ql.Date(15, 6, 2029), ql.Period(ql.Annual),
                    ql.NullCalendar(), ql.Unadjusted, ql.Unadjusted,
                    ql.DateGeneration.Backward, False)
bond = ql.FixedRateBond(0, 100.0, sched, [0.03], dc)       # 工具：只描述条款
bond.setPricingEngine(ql.DiscountingBondEngine(curve))     # 引擎：决定如何定价

bond.cleanPrice()        # 100.0
q.setValue(0.04)         # 只修改报价，不重建任何对象
bond.cleanPrice()        # 97.2249，与例3.1 一致

ql.Settings.instance().evaluationDate = ql.Date(15, 12, 2026)   # 估值日后移半年
curve.referenceDate()    # Date(15,12,2026)：以结算天数构造的曲线随估值日移动
bond.accruedAmount()     # 1.5，半个付息期的应计利息
bond.dirtyPrice()        # 99.1503
```

!!! note "Python 绑定与 C++ 的差异"
    - **命名**：C++ 的 `Bond::yield` 因 `yield` 是 Python 关键字，在 Python 中改名为 `bondYield`；C++ 模板类被实例化为具体类名，如 `PiecewiseYieldCurve<Discount, LogLinear>` 对应 `ql.PiecewiseLogLinearDiscount`。
    - **句柄**：C++ 的 `Handle<YieldTermStructure>` 在 Python 中为 `ql.YieldTermStructureHandle`，可重新链接的版本为 `ql.RelinkableYieldTermStructureHandle`；`Handle<Quote>` 为 `ql.QuoteHandle`。
    - **查签名**：SWIG 生成的函数多为重载，Python 的 `help()` 往往只显示 `*args`。以错误参数调用时，报错信息会列出全部 C++ 原型（`Possible C/C++ prototypes are: ...`），这是核对本机版本实际签名最可靠的办法。
    - **日期互转**：`ql.Date.from_date(datetime.date(...))` 与 `d.to_date()` 在 `datetime.date` 与 `ql.Date` 之间转换，便于与 `fi` 的接口对接。

---

## B.2 日期、日历与付息日程

### B.2.1 Date 与 Period

`ql.Date(日, 月, 年)` 的参数顺序为"日、月、年"。日期加减 `Period` 按日历月推算，月末日期遇到较短月份时截断至月末；两个日期相减得到实际天数。

```python
import datetime as dt
import QuantLib as ql

d = ql.Date(15, 6, 2026)
d + ql.Period(3, ql.Months)                     # Date(15,9,2026)
d + ql.Period("6M")                             # Date(15,12,2026)，也可用字符串写期限
ql.Date(31, 1, 2026) + ql.Period(1, ql.Months)  # Date(28,2,2026)，月末截断
ql.Date(15, 9, 2026) - ql.Date(15, 3, 2026)     # 184，实际天数
d.weekday()                                     # 2（1=周日，2=周一，……，7=周六）
d.ISO()                                         # '2026-06-15'
ql.Date.from_date(dt.date(2026, 6, 15)) == d    # True
ql.Date.isLeap(2028)                            # True
```

### B.2.2 Calendar：NullCalendar 与 China(IB/SSE)

`Calendar` 判断某日是否为营业日，并按营业日惯例调整日期。本书用到两类日历：

- `ql.NullCalendar()`：每天都是营业日，不做任何调整。用于复现教科书的"名义付息日"。
- `ql.China(ql.China.IB)` 与 `ql.China(ql.China.SSE)`：分别对应银行间市场与上海证券交易所。

实测表明，两者的法定节假日相同，区别在于**调休工作日**：法定节假日调休而安排在周六、周日上班的日子，`China.IB` 视为营业日，`China.SSE` 仍视为休市日（交易所周末不开市）。因此 IB 日历每年的营业日通常比 SSE 多若干天（2026年分别为248天与242天）。

```python
import QuantLib as ql

ib, sse = ql.China(ql.China.IB), ql.China(ql.China.SSE)
d = ql.Date(14, 2, 2026)                         # 周六，春节调休工作日
ib.isBusinessDay(d), sse.isBusinessDay(d)        # (True, False)
ib.isBusinessDay(ql.Date(17, 2, 2026))           # False，春节假期，两者均休
ib.businessDaysBetween(ql.Date(30, 9, 2026), ql.Date(12, 10, 2026))    # 4（含 10-10 周六调休）
sse.businessDaysBetween(ql.Date(30, 9, 2026), ql.Date(12, 10, 2026))   # 3
len(sse.holidayList(ql.Date(1, 1, 2026), ql.Date(31, 12, 2026), False))  # 19，工作日中的节假日数
len(sse.holidayList(ql.Date(1, 1, 2027), ql.Date(31, 12, 2027), False))  # 1，仅录入元旦
```

!!! warning "节假日表只覆盖已公布的年份"
    中国节假日每年由国务院办公厅公布，QuantLib 只能录入已公布的安排。在 QuantLib 1.42.1 中，`China` 日历完整录入至2026年，2027年只有元旦，2028年及以后只按周末判断。对远期付息日而言，这意味着 `China(IB)` + `Following` 的结果在节假日附近可能与日后的实际安排不同。长期限债券的日程若需精确，应以登记托管机构公布的付息日为准，或用 `cal.addHoliday(...)`、`cal.removeHoliday(...)` 补录。

### B.2.3 营业日调整惯例

| 惯例 | 含义 | 本书用法 |
|---|---|---|
| `ql.Unadjusted` | 不调整 | 与 `NullCalendar` 搭配复现名义日期（第2、4、5、8～10、12、13章） |
| `ql.Following` | 顺延至下一营业日 | 第3、6章的 `China(IB)` 日程 |
| `ql.ModifiedFollowing` | 顺延，但若跨月则改为提前 | 互换、存款等货币市场惯例 |
| `ql.Preceding` | 提前至上一营业日 | 较少使用 |

```python
import QuantLib as ql

cal = ql.China(ql.China.IB)
for name, conv in [("Unadjusted", ql.Unadjusted), ("Following", ql.Following),
                   ("ModifiedFollowing", ql.ModifiedFollowing), ("Preceding", ql.Preceding)]:
    print(name, cal.adjust(ql.Date(15, 3, 2026), conv).ISO(),
          cal.adjust(ql.Date(31, 5, 2026), conv).ISO(), cal.adjust(ql.Date(1, 10, 2026), conv).ISO())
# Unadjusted 2026-03-15 2026-05-31 2026-10-01
# Following 2026-03-16 2026-06-01 2026-10-08
# ModifiedFollowing 2026-03-16 2026-05-29 2026-10-08
# Preceding 2026-03-13 2026-05-29 2026-09-30
```

2026-03-15 与 2026-05-31 均为周日，2026-10-01 至 10-07 为国庆假期。2026-05-31 顺延将跨入6月，故 `ModifiedFollowing` 改为提前至 05-29。

### B.2.4 Schedule 与 DateGeneration

`ql.Schedule(起息日, 到期日, 付息周期, 日历, 付息日调整, 到期日调整, 生成规则, 月末规则)` 生成付息日序列。`DateGeneration.Backward` 从到期日向前倒推，不规则的短期出现在首期，这是债券的常见做法；`Forward` 从起息日向后推，短期出现在末期。

```python
import QuantLib as ql

def dates(start, end, tenor, cal, conv, rule):
    s = ql.Schedule(start, end, tenor, cal, conv, conv, rule, False)
    return [d.ISO() for d in s]

null, ib = ql.NullCalendar(), ql.China(ql.China.IB)
dates(ql.Date(15, 6, 2026), ql.Date(15, 3, 2029), ql.Period(ql.Annual), null, ql.Unadjusted,
      ql.DateGeneration.Backward)
# ['2026-06-15', '2027-03-15', '2028-03-15', '2029-03-15']：首期为短期
dates(ql.Date(15, 6, 2026), ql.Date(15, 3, 2029), ql.Period(ql.Annual), null, ql.Unadjusted,
      ql.DateGeneration.Forward)
# ['2026-06-15', '2027-06-15', '2028-06-15', '2029-03-15']：末期为短期
dates(ql.Date(15, 3, 2026), ql.Date(15, 3, 2028), ql.Period(ql.Semiannual), ib, ql.Following,
      ql.DateGeneration.Backward)
# ['2026-03-16', '2026-09-15', '2027-03-15', '2027-09-15', '2028-03-15']：周日顺延
```

`Schedule` 可直接迭代或用 `list(sched)` 取出日期；`sched[i]`、`len(sched)`、`sched.isRegular(i)` 分别返回第 i 个日期、日期个数和第 i 期是否为规则期。最后一个参数 `endOfMonth=True` 时，起息日为月末的日程会保持在各月月末（如 11-30、05-31）。

---

## B.3 计息惯例 DayCounter

`DayCounter.yearFraction(d1, d2)` 返回区间的年化分数，`dayCount(d1, d2)` 返回按该惯例计的天数。本书用到的计息惯例及其与 `fi.cashflow.year_fraction`（第2章）的对应关系如下：

| QuantLib 类 | 含义 | 对应的 `fi` 写法 | 本书用法 |
|---|---|---|---|
| `ActualActual(ActualActual.ISDA)` | 按公历年拆分，闰年部分以366为分母 | `"ACT/ACT"` | 第2～6、9章 |
| `ActualActual(ActualActual.ISMA)` | 实际天数 / (付息频率 × 参考付息期天数)，即 ICMA 口径 | `accrued_interest(..., "ACT/ACT")` 的 $t/TS$ | 第2章应计利息 |
| `ActualActual(ActualActual.Bond)` | 与 ISMA 相同（同一子约定的别名） | — | — |
| `Actual365Fixed()` | 实际天数 / 365 | `"ACT/365"` | 第8、10～14章 |
| `Actual360()` | 实际天数 / 360 | `"ACT/360"` | 货币市场 |
| `Thirty360(Thirty360.BondBasis)` | 30/360，起日31日改30日，起日为30日时止日31日改30日 | `"30/360"` | 本附录对拍 |
| `Thirty360(Thirty360.USA)` | 在 BondBasis 基础上增加2月末规则 | `"30/360"`（2月末除外） | 第2章 |
| `Thirty360(Thirty360.European)` | 30E/360，起止日为31日一律改30日 | — | — |

下面用三个区间实测比较：

```python
import datetime as dt
import QuantLib as ql
from fi import cashflow as cf

pairs = {"ACT/ACT": ql.ActualActual(ql.ActualActual.ISDA), "ACT/365": ql.Actual365Fixed(),
         "ACT/360": ql.Actual360(), "30/360": ql.Thirty360(ql.Thirty360.BondBasis)}
for s, e in [(dt.date(2026, 3, 15), dt.date(2026, 9, 15)),
             (dt.date(2027, 12, 15), dt.date(2028, 6, 15)),
             (dt.date(2026, 2, 28), dt.date(2026, 8, 31))]:
    q1, q2 = ql.Date.from_date(s), ql.Date.from_date(e)
    print(s, e, [(k, round(cf.year_fraction(s, e, k), 6), round(v.yearFraction(q1, q2), 6))
                 for k, v in pairs.items()])
# 每组括号内依次为：惯例、fi 结果、QuantLib 结果；三组区间上 fi 与 QuantLib 逐项相同
```

实测结果汇总如下（实际天数分别为184、183、184天）：

| 区间 | ISDA | ACT/365F | ACT/360 | 30/360 BondBasis | 30/360 USA | 30E/360 | `fi` |
|---|---|---|---|---|---|---|---|
| 2026-03-15→2026-09-15 | 0.504110 | 0.504110 | 0.511111 | 0.500000 | 0.500000 | 0.500000 | 与左侧对应列一致 |
| 2027-12-15→2028-06-15（跨闰日） | 0.500127 | 0.501370 | 0.508333 | 0.500000 | 0.500000 | 0.500000 | 与左侧对应列一致 |
| 2026-02-28→2026-08-31（2月末起息） | 0.504110 | 0.504110 | 0.511111 | 0.508333 | 0.500000 | 0.505556 | `"30/360"` 为 0.508333 |

第一行即第2章例2.3（ISDA 与 ACT/365F 均为 0.504110，30/360 为 0.5）。第三行显示，同为"30/360"，三种子约定在2月末和31日附近给出三个不同结果；`fi` 的简化实现与 `BondBasis` 一致，而与 `USA` 的2月末规则不同，这正是第2章"`fi.cashflow` 的实现边界"所提示的情形。

!!! warning "ISMA 必须给出参考付息期"
    `ActualActual(ISMA)` 的分母取决于"参考付息期"。单独调用 `yearFraction(d1, d2)` 而不给参考期时，QuantLib 把区间本身当作参考期，结果按月数取整，往往没有意义：

    ```python
    import QuantLib as ql

    isma = ql.ActualActual(ql.ActualActual.ISMA)
    isma.yearFraction(ql.Date(15, 3, 2026), ql.Date(31, 8, 2026))   # 0.5，未给参考期，结果无意义
    isma.yearFraction(ql.Date(15, 11, 2027), ql.Date(15, 2, 2028),
                      ql.Date(15, 11, 2027), ql.Date(15, 5, 2028))  # 0.252747 = 0.5 × 92/182
    ```

    在 `FixedRateBond` 中使用 ISMA 时，债券会把每期的起止日作为参考期自动传入，故无此问题。也可用 `ql.ActualActual(ql.ActualActual.ISMA, sched)` 把日程直接交给计息惯例。

同一笔应计利息，在三种 ACT/ACT 处理下结果不同。以第2章的跨闰年付息期（2027-11-15 至 2028-05-15，结算日 2028-02-15，票面利率3%、半年付息）为例：

```python
import QuantLib as ql

ql.Settings.instance().evaluationDate = ql.Date(15, 2, 2028)
sched = ql.Schedule(ql.Date(15, 11, 2027), ql.Date(15, 11, 2029), ql.Period(ql.Semiannual),
                    ql.NullCalendar(), ql.Unadjusted, ql.Unadjusted,
                    ql.DateGeneration.Backward, False)
for name, dc in [("ISMA", ql.ActualActual(ql.ActualActual.ISMA)),
                 ("ISDA", ql.ActualActual(ql.ActualActual.ISDA))]:
    bond = ql.FixedRateBond(0, 100.0, sched, [0.03], dc)
    print(name, round(bond.accruedAmount(ql.Date(15, 2, 2028)), 6),
          round(bond.cashflows()[0].amount(), 6))
# ISMA 0.758242 1.5       ← 与 fi.accrued_interest(..., "ACT/ACT") 相同（t/TS = 92/182）
# ISDA 0.755154 1.492859  ← 应计与当期票息都按 ISDA 年化分数计算
```

由此得到三个数字：ISMA（$t/TS$）为 0.758242，与 `fi` 及第2章一致；"两个 ISDA 年化分数之比"为第2章给出的 0.758766；以 ISDA 为计息惯例构造的 `FixedRateBond` 则得到 0.755154，且当期票息也不再恰为 1.5。对拍应计利息时，必须先确定采用哪一种口径。

---

## B.4 利率与期限结构

### B.4.1 InterestRate 与 Compounding

`ql.InterestRate(利率, 计息惯例, 复利方式, 频率)` 封装一个带口径的利率，可计算折现因子、复利因子，并在不同复利方式之间换算等价利率。复利方式有 `ql.Simple`（单利）、`ql.Compounded`（按频率离散复利）、`ql.Continuous`（连续复利）与 `ql.SimpleThenCompounded`（一期内单利、超过一期复利）。

```python
import math
import QuantLib as ql

r = ql.InterestRate(0.03, ql.Actual365Fixed(), ql.Compounded, ql.Annual)
r.discountFactor(1.0)                                         # 0.970874 = 1/1.03
r.compoundFactor(2.0)                                         # 1.0609 = 1.03^2
r.equivalentRate(ql.Continuous, ql.Annual, 1.0).rate()        # 0.029559
math.log(1.03)                                                # 0.029559
r.equivalentRate(ql.Compounded, ql.Semiannual, 1.0).rate()    # 0.029778，半年复利等价利率
```

第3、4、6章用 `InterestRate` 把统一收益率连同口径一起交给 `BondFunctions`（B.5）。

### B.4.2 FlatForward：默认连续复利

`ql.FlatForward(参考日, 利率, 计息惯例[, 复利方式, 频率])` 构造平坦曲线。**省略复利方式时默认连续复利**，这是第12、13章对拍差异的主要来源。

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc = ql.Actual365Fixed()
d5 = today + ql.Period(5, ql.Years)
ff_c = ql.FlatForward(today, 0.03, dc)                            # 默认连续复利
ff_a = ql.FlatForward(today, 0.03, dc, ql.Compounded, ql.Annual)  # 年复利

dc.yearFraction(today, d5)                                # 5.002740，5年中含 2028-02-29
ff_c.discount(d5)                                         # 0.860637 = exp(-0.03 × 5.002740)
ff_a.discount(d5)                                         # 0.862539
ff_a.discount(5.0)                                        # 0.862609 = 1.03^-5，按年数取值
ff_c.zeroRate(d5, dc, ql.Compounded, ql.Annual).rate()    # 0.030455，连续3%折合年复利
ff_c.forwardRate(today + ql.Period(1, ql.Years), today + ql.Period(15, ql.Months),
                 dc, ql.Simple).rate()                    # 0.030114，1年后起3个月的单利远期
```

连续复利 3% 折合年复利为 3.0455%，与第12章 `VanillaSwap.fairRate()` 的 3.0455% 相同，这并非巧合：平坦曲线上的平价互换利率近似等于该曲线的年复利零息利率。第11章的远期利率即上面最后一行的用法（该章曲线为 2.5%，结果为 2.5079%）。

曲线对象既可按日期取值（`discount(date)`、`zeroRate(date, dc, comp, freq)`），也可按年数取值（`discount(t)`、`zeroRate(t, comp)`）；后者跳过计息惯例，直接使用给定的 $t$。

### B.4.3 ZeroCurve 与 DiscountCurve

已知若干期限的零息利率或折现因子时，可用 `ZeroCurve(日期, 零息利率, 计息惯例, 日历, 插值, 复利方式, 频率)` 或 `DiscountCurve(日期, 折现因子, 计息惯例)` 直接构造曲线，节点之间按指定方法插值。

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc = ql.Actual365Fixed()
dates = [today + ql.Period(n, ql.Years) for n in (0, 1, 2, 3)]
zc = ql.ZeroCurve(dates, [0.02, 0.02, 0.025063, 0.028132], dc, ql.NullCalendar(),
                  ql.Linear(), ql.Compounded, ql.Annual)
zc.zeroRate(dates[3], dc, ql.Compounded, ql.Annual).rate()   # 0.028132，节点处原样返回
zc.discount(dates[3])                                        # 0.920069
```

`ZeroCurve` 的第一个日期须为参考日；节点处的利率按日期计的年化分数解释，故在含闰日的区间上，折现因子与"整年"公式 $(1+z)^{-3}=0.920138$ 略有差别。

### B.4.4 分段 bootstrap：PiecewiseYieldCurve

第5章用 `FixedRateBondHelper` 把平价国债包装成 RateHelper，再由分段曲线联立 bootstrap。分段曲线类名的格式为 `Piecewise` + 插值方式 + 插值对象，常用的有 `PiecewiseLogLinearDiscount`（对折现因子取对数线性插值，第5章所用）、`PiecewiseLogCubicDiscount`、`PiecewiseLinearZero`、`PiecewiseCubicZero` 与 `PiecewiseFlatForward`。

```python
import QuantLib as ql
from fi import curve

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc = ql.ActualActual(ql.ActualActual.ISDA)
helpers = []
for n, par in [(1, 0.02), (2, 0.025), (3, 0.028)]:
    sched = ql.Schedule(today, today + ql.Period(n, ql.Years), ql.Period(ql.Annual),
                        ql.NullCalendar(), ql.Unadjusted, ql.Unadjusted,
                        ql.DateGeneration.Backward, False)
    helpers.append(ql.FixedRateBondHelper(ql.QuoteHandle(ql.SimpleQuote(100.0)), 0, 100.0,
                                          sched, [par], dc, ql.Unadjusted))

d3, d25 = today + ql.Period(3, ql.Years), today + ql.Period(30, ql.Months)
for cls in (ql.PiecewiseLogLinearDiscount, ql.PiecewiseLogCubicDiscount, ql.PiecewiseLinearZero):
    yc = cls(today, helpers, dc)
    print(cls.__name__, round(yc.zeroRate(d3, dc, ql.Compounded, ql.Annual).rate(), 6),
          round(yc.zeroRate(d25, dc, ql.Compounded, ql.Annual).rate(), 6))
# PiecewiseLogLinearDiscount 0.028133 0.026905
# PiecewiseLogCubicDiscount 0.028133 0.026841
# PiecewiseLinearZero 0.028133 0.026599

zeros, _ = curve.bootstrap([0.02, 0.025, 0.028])
zeros[2], curve.interpolate([1, 2, 3], zeros, t=2.5, method="linear")   # (0.028132, 0.026598)
```

节点处三种曲线相同，与 `fi.curve.bootstrap` 的结果（0.0281325）相差约 $1\times10^{-7}$，四舍五入至六位小数后分别显示为 0.028133 与 0.028132；节点之间则取决于插值方式：对零息利率线性插值的 `PiecewiseLinearZero` 在 2.5 年处为 0.026599，与 `fi` 的线性插值 0.026598 基本一致，而第5章所用的对数线性折现因子插值为 0.026905。这印证了第5章"插值方式会带来小数后几位差异"的说明。曲线默认不外推，查询最后节点之后的日期前须调用 `yc.enableExtrapolation()`。

### B.4.5 互换曲线：SwapRateHelper

互换报价用 `ql.SwapRateHelper(报价, 期限, 日历, 固定腿频率, 固定腿调整, 固定腿计息惯例, 浮动指数)` 包装。浮动指数若不带预测曲线，bootstrap 时会自动以正在构建的曲线作为预测曲线（单曲线）。下例复现第12章例12.4：

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
cal = ql.NullCalendar()
for dc in (ql.Thirty360(ql.Thirty360.BondBasis), ql.Actual365Fixed()):
    idx = ql.IborIndex("Idx", ql.Period(1, ql.Years), 0, ql.CNYCurrency(), cal,
                       ql.Unadjusted, False, dc)                 # 不带曲线：单曲线 bootstrap
    helpers = [ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(r)), ql.Period(n, ql.Years),
                                 cal, ql.Annual, ql.Unadjusted, dc, idx)
               for n, r in [(1, 0.024), (2, 0.026), (3, 0.028), (4, 0.030), (5, 0.031)]]
    yc = ql.PiecewiseLogLinearDiscount(today, helpers, dc)
    print(dc.name(), [round(yc.discount(today + ql.Period(n, ql.Years)), 6) for n in range(1, 6)])
# 30/360 (Bond Basis) [0.976563, 0.949912, 0.920291, 0.887958, 0.857637]
# Actual/365 (Fixed) [0.976563, 0.949846, 0.920222, 0.887886, 0.857565]
```

以 30/360 计息时各期 $\tau$ 恰为1，结果与例12.4 的折现因子一致（例12.4 中 1 年期的 0.976562 为 $1/1.024=0.9765625$ 的截断写法）；改用 Actual365Fixed 后，第2期起因跨2028闰年而出现小差异。

### B.4.6 Quote 与 Handle

| 类 | 作用 | 本书用法 |
|---|---|---|
| `SimpleQuote(v)` | 可修改的报价，`setValue(v)` 改值并通知下游 | 第5、10、13、14章 |
| `QuoteHandle(q)` | 报价的句柄，供曲线、引擎引用 | 同上 |
| `YieldTermStructureHandle(ts)` | 曲线的句柄，引擎与指数均通过句柄引用曲线 | 第8～13章 |
| `RelinkableYieldTermStructureHandle()` | 可用 `linkTo(ts)` 切换所指曲线 | 情景分析 |
| `BlackVolTermStructureHandle(vol)` | 股票波动率曲面的句柄 | 第10章 |

---

## B.5 固定利率债券

### B.5.1 FixedRateBond 与 BondFunctions

`ql.FixedRateBond(结算天数, 面值, 日程, [票面利率], 计息惯例)` 构造固息债。给定收益率求价格、给定价格求收益率、求久期凸性等不依赖引擎的计算，由 `ql.BondFunctions` 的静态函数完成。下例统一了第3、4、6章的同一只债券（3年期、年付息、票面利率3%）：

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc = ql.ActualActual(ql.ActualActual.ISDA)
sched = ql.Schedule(today, today + ql.Period(3, ql.Years), ql.Period(ql.Annual),
                    ql.NullCalendar(), ql.Unadjusted, ql.Unadjusted,
                    ql.DateGeneration.Backward, False)
bond = ql.FixedRateBond(0, 100.0, sched, [0.03], dc)
[round(c.amount(), 6) for c in bond.cashflows()]   # [3.0, 3.004491, 2.995509, 100.0]

y4 = ql.InterestRate(0.04, dc, ql.Compounded, ql.Annual)
ql.BondFunctions.cleanPrice(bond, y4)              # 97.2249（例3.1，fi 为 97.2249）
bond.dirtyPrice(0.04, dc, ql.Compounded, ql.Annual)                 # 97.2249，估值日恰为付息日
bond.bondYield(ql.BondPrice(97.2249, ql.BondPrice.Clean),
               dc, ql.Compounded, ql.Annual)       # 0.0400000（第4章，fi 为 0.04）

y3 = ql.InterestRate(0.03, dc, ql.Compounded, ql.Annual)
ql.BondFunctions.duration(bond, y3, ql.Duration.Macaulay)   # 2.913471（第6章，fi 为 2.9135）
ql.BondFunctions.duration(bond, y3, ql.Duration.Modified)   # 2.828613（fi 为 2.8286）
ql.BondFunctions.convexity(bond, y3)                        # 10.876648（fi 为 10.877）
ql.BondFunctions.basisPointValue(bond, y3)                  # -0.028286（fi.dv01 为 +0.02829）
```

几点说明：

- **票息不等**：ISDA 按公历年拆分，第2期（2027-06-15 至 2028-06-15）跨2028闰年，票息为 3.004491 而非 3.0。这就是第4章所说"票息金额也会略有变化"，也是 QuantLib 与 `fi` 的净价相差约 $3\times10^{-6}$（97.224906 vs 97.224909）、收益率相差约 $2\times10^{-8}$ 的原因。若改用 `ActualActual(ISMA)`，各期票息恰为 3.0。
- **符号约定**：`basisPointValue` 返回收益率上升 1bp 时的价格变化，符号为负；`fi.risk.dv01` 报告的是价格下降的绝对值，符号为正。
- **净价与全价**：`BondFunctions.cleanPrice` 支持 `InterestRate` 参数；全价则用债券自身的方法 `bond.dirtyPrice(收益率, 计息惯例, 复利方式, 频率)`。本机 1.42.1 中 `BondFunctions.dirtyPrice` 只接受期限结构参数，不接受 `InterestRate`。
- **第6章原文设置**：第6章以 2026-06-11 为估值日、使用 `China(IB)` + `Following`（2028-06-11 为周日，顺延至 06-12），实测麦考利久期 2.913474、修正久期 2.828615、凸性 10.876590，与上面的差异均小于 $10^{-4}$。
- **价格对象**：`ql.BondPrice(数值, ql.BondPrice.Clean)` 或 `ql.BondPrice.Dirty` 用于明确传入的是净价还是全价，`bondYield` 与第9章的 `Callability` 都要求这一类型。

`BondFunctions` 中本书用到或常用的函数还包括 `accruedAmount(bond, date)`、`accruedDays(bond, date)`、`accrualDays(bond, date)`、`zSpread(...)` 与 `nextCashFlowDate(bond)`。

### B.5.2 DiscountingBondEngine

按一条曲线贴现定价时，给债券挂上 `DiscountingBondEngine(曲线句柄)`，再调用 `NPV()`、`cleanPrice()`、`dirtyPrice()`、`accruedAmount()`：

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc = ql.ActualActual(ql.ActualActual.ISDA)
sched = ql.Schedule(today, today + ql.Period(3, ql.Years), ql.Period(ql.Annual),
                    ql.NullCalendar(), ql.Unadjusted, ql.Unadjusted,
                    ql.DateGeneration.Backward, False)
bond = ql.FixedRateBond(0, 100.0, sched, [0.03], dc)

annual = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dc, ql.Compounded, ql.Annual))
bond.setPricingEngine(ql.DiscountingBondEngine(annual))
bond.cleanPrice()        # 97.2249，与统一收益率 4% 的结果相同

cont = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dc))   # 省略复利方式
bond.setPricingEngine(ql.DiscountingBondEngine(cont))
bond.cleanPrice()        # 97.0045，连续复利 4% 折现，价格更低
```

### B.5.3 应计利息与营业日调整

第2章的应计利息对拍，以及"营业日调整使付息期从184天变为183天"的提示，可用下面的代码复现：

```python
import QuantLib as ql

ql.Settings.instance().evaluationDate = ql.Date(15, 6, 2026)
dc = ql.ActualActual(ql.ActualActual.ISMA)
for cal, conv in [(ql.NullCalendar(), ql.Unadjusted), (ql.China(ql.China.IB), ql.Following)]:
    sched = ql.Schedule(ql.Date(15, 3, 2026), ql.Date(15, 3, 2029), ql.Period(ql.Semiannual),
                        cal, conv, conv, ql.DateGeneration.Backward, False)
    bond = ql.FixedRateBond(0, 100.0, sched, [0.03], dc)
    d = ql.Date(15, 6, 2026)
    print(cal.name(), round(bond.accruedAmount(d), 6),
          ql.BondFunctions.accruedDays(bond, d), ql.BondFunctions.accrualDays(bond, d))
# Null 0.75 92 184                         ← 例2.4，与 fi 一致
# China inter bank market 0.745902 91 183  ← 起息日 03-15（周日）顺延至 03-16
```

---

## B.6 浮息债与利率互换

### B.6.1 自定义 IborIndex

QuantLib 内置的 `Shibor` 等指数带有固定的日历和惯例。本书为使对拍条件透明，统一用 `ql.IborIndex` 自定义指数：

```text
ql.IborIndex(名称, 期限, 定盘天数, 货币, 日历, 营业日调整, 月末规则, 计息惯例[, 预测曲线句柄])
```

第8章取 `ql.Period(3, ql.Months)`，第12、13章取 `ql.Period(1, ql.Years)`，货币均为 `ql.CNYCurrency()`、日历为 `NullCalendar`、定盘天数为0。最后一个参数是**预测曲线**，指数据此投影未来定盘利率；不传时为空句柄，只能用于 bootstrap（B.4.5）或已录入历史定盘的情形。

### B.6.2 FloatingRateBond

```python
import QuantLib as ql
from fi import frn

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc = ql.Actual365Fixed()
fwd = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.02, dc))            # 基准曲线 2%
idx = ql.IborIndex("MyIbor", ql.Period(3, ql.Months), 0, ql.CNYCurrency(),
                   ql.NullCalendar(), ql.Unadjusted, False, dc, fwd)
sched = ql.Schedule(today, today + ql.Period(2, ql.Years), ql.Period(3, ql.Months),
                    ql.NullCalendar(), ql.Unadjusted, ql.Unadjusted,
                    ql.DateGeneration.Backward, False)
bond = ql.FloatingRateBond(0, 100.0, sched, idx, dc, ql.Unadjusted, 0,
                           [1.0], [0.005], [], [], False, 100.0, today)       # QM = 50bp
disc = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.025, dc))          # 基准 + DM
bond.setPricingEngine(ql.DiscountingBondEngine(disc))
bond.cleanPrice()                              # 99.9945（第8章写作 ≈ 99.99）
frn.price_frn(0.02, 0.005, 0.005, 8, 4)        # 100.0

c0 = ql.as_floating_rate_coupon(bond.cashflows()[0])
c0.fixingDate(), c0.indexFixing()              # (Date(15,6,2026), 0.020050)：首期由曲线投影
```

`FloatingRateBond` 的参数依次为：结算天数、面值、日程、指数、计息惯例、付息调整、定盘天数、乘数（gearings）、利差（spreads）、上限（caps）、下限（floors）、是否后置定盘（in arrears）、赎回价、发行日。`ql.as_floating_rate_coupon` 把现金流转换为浮息票息对象，可查看每期定盘日、定盘利率与票息率。

!!! tip "浮息债偏离面值的主要原因是复利方式"
    上例中 DM = QM 却未精确回到面值，主要原因是两条 `FlatForward` 都采用默认的连续复利：连续复利 2% 投影出的季度单利远期约为 2.005%，而 `fi.frn` 的"基准恒定"模型按季度离散复利处理。把预测曲线与折现曲线都改为 `ql.Compounded, ql.Quarterly` 后，价格为 99.999992，剩余差异仅来自 Actual365Fixed 下各季度 $\tau$ 不恰为 0.25。

**首期定盘（fixing）。** 定盘日不晚于估值日的票息需要历史定盘利率。当定盘日恰为估值日且未录入定盘值时，QuantLib 1.42.1 默认用预测曲线投影（`ql.Settings.instance().enforcesTodaysHistoricFixings` 默认为 `False`）；定盘日早于估值日而缺少定盘值时则会报错。录入已知定盘用 `idx.addFixing(日期, 利率)`，清除用 `ql.IndexManager.instance().clearHistories()`。在上例中录入 `idx.addFixing(today, 0.018)` 后，首期票息率变为 2.3%，净价变为 99.9431。

### B.6.3 VanillaSwap 与 DiscountingSwapEngine

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc, cal = ql.Actual365Fixed(), ql.NullCalendar()
disc = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.03, dc))    # 默认连续复利
idx = ql.IborIndex("Idx", ql.Period(1, ql.Years), 0, ql.CNYCurrency(), cal,
                   ql.Unadjusted, False, dc, disc)
sched = ql.Schedule(today, today + ql.Period(5, ql.Years), ql.Period(1, ql.Years), cal,
                    ql.Unadjusted, ql.Unadjusted, ql.DateGeneration.Forward, False)
swap = ql.VanillaSwap(ql.VanillaSwap.Payer, 1e8, sched, 0.025, dc, sched, idx, 0.0, dc)
swap.setPricingEngine(ql.DiscountingSwapEngine(disc))
swap.NPV()            # 2,496,143（第12章）
swap.fairRate()       # 0.030455
swap.fixedLegBPS()    # -45,761：固定腿利率变动 1bp 的价值变化，付固定方为负
swap.fixedLegNPV(), swap.floatingLegNPV()   # (-11,440,134, 13,936,276)
```

`VanillaSwap` 的参数依次为：方向（`ql.VanillaSwap.Payer` 付固定、`ql.VanillaSwap.Receiver` 收固定）、名义本金、固定腿日程、固定利率、固定腿计息惯例、浮动腿日程、浮动指数、浮动腿利差、浮动腿计息惯例。`fairRate()` 为平价互换利率，`fairSpread()` 为使 NPV 为零的浮动腿利差，`fixedLegBPS()` 的绝对值即固定腿年金乘以名义本金再乘以 1bp，可与 `fi.swap.swap_dv01` 对照。

第12章指出差异的主因是复利方式。逐项统一后可完全复现 `fi`：

| 设置 | NPV（元） | fairRate | `fixedLegBPS`（元） |
|---|---|---|---|
| 第12章原设置（连续复利，ACT/365F） | 2,496,143 | 3.0455% | −45,761 |
| 改为年复利（ACT/365F） | 2,291,114 | 3.0000% | −45,820 |
| 年复利 + `Thirty360(BondBasis)` | 2,289,854 | 3.0000% | −45,797 |
| `fi.swap`（整年、年复利） | 2,289,854 | 3.0000% | 45,797（`swap_dv01`） |

第三行与 `fi` 一致，说明第12章所述"剩余约1,260元来自日计数与闰年"是准确的（2,291,114 − 2,289,854 = 1,260）。

---

## B.7 含权债与可转债

### B.7.1 CallableFixedRateBond 与 Hull–White 树

赎回（回售）条款用 `ql.Callability(价格, 类型, 日期)` 逐条描述，放入 `ql.CallabilitySchedule()`；类型为 `ql.Callability.Call`（赎回）或 `ql.Callability.Put`（回售），价格须用 `ql.BondPrice` 注明净价或全价。下例为第9章例9.2 对应的 QuantLib 版本：

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc = ql.ActualActual(ql.ActualActual.ISDA)
curve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.03, dc))
sched = ql.Schedule(today, today + ql.Period(6, ql.Years), ql.Period(ql.Annual),
                    ql.NullCalendar(), ql.Unadjusted, ql.Unadjusted,
                    ql.DateGeneration.Backward, False)
calls = ql.CallabilitySchedule()
for n in range(1, 6):
    calls.append(ql.Callability(ql.BondPrice(100.0, ql.BondPrice.Clean),
                                ql.Callability.Call, today + ql.Period(n, ql.Years)))
bond = ql.CallableFixedRateBond(0, 100.0, sched, [0.06], dc, ql.Unadjusted,
                                100.0, today, calls)
bond.setPricingEngine(ql.TreeCallableFixedRateBondEngine(ql.HullWhite(curve, 0.03, 0.015), 100))
mkt = bond.cleanPrice()          # 102.6943（第9章：约 102.69）

for sigma in (0.005, 0.015, 0.030):
    bond.setPricingEngine(ql.TreeCallableFixedRateBondEngine(ql.HullWhite(curve, 0.03, sigma), 100))
    oas = bond.OAS(mkt, curve, dc, ql.Compounded, ql.Annual, today, 1e-10, 200, 0.0)
    print(f"sigma={sigma:.1%}  OAS={oas * 1e4:.2f} bp")
# sigma=0.5%  OAS=17.36 bp
# sigma=1.5%  OAS=0.00 bp
# sigma=3.0%  OAS=-105.04 bp

bond.setPricingEngine(ql.TreeCallableFixedRateBondEngine(ql.HullWhite(curve, 0.03, 0.015), 100))
bond.effectiveDuration(0.0, curve, dc, ql.Compounded, ql.Annual)   # 1.2545
```

- `CallableFixedRateBond` 的参数依次为：结算天数、面值、日程、票面利率、计息惯例、付息调整、赎回价、发行日、赎回日程。
- `ql.HullWhite(曲线句柄, a, sigma)` 中 `a` 为均值回复速度，`sigma` 为短利率的绝对波动参数；`TreeCallableFixedRateBondEngine(模型, 时间步数)` 在三叉树上反向归纳。
- `OAS(净价, 曲线, 计息惯例, 复利方式, 频率, 结算日, 精度, 最大迭代次数, 初值)` 返回小数形式的期权调整利差；`cleanPriceOAS(oas, ...)`、`effectiveDuration(oas, ...)`、`effectiveConvexity(oas, ...)` 的参数格式相同。
- Hull–White 模型下的有效久期 1.2545 与 `fi.tree` 例9.2 的 0.9709 不同，原因同第9章 warning：两种模型的 `sigma` 含义不同、树的构造与曲线校准方式也不同，只宜比较定性结论。

### B.7.2 ConvertibleFixedCouponBond

QuantLib 1.42.1 中可转债类的构造方式为：

```text
ql.ConvertibleFixedCouponBond(行权方式, 转股比例, 赎回日程, 发行日, 结算天数,
                              [票面利率], 计息惯例, 日程[, 赎回价])
```

较早版本曾把分红日程与信用利差作为债券构造参数；在本机版本中，二者已移至定价引擎 `ql.BinomialConvertibleEngine(过程, 树类型, 步数, 信用利差句柄, 分红日程)`。网上较早的示例若按旧签名构造会直接报错，应以本机报错信息列出的原型为准（B.1）。

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc, cal = ql.Actual365Fixed(), ql.NullCalendar()
spot = ql.QuoteHandle(ql.SimpleQuote(8.0))                                   # 正股价格
rTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.03, dc))           # 无风险利率
qTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.0, dc))            # 股息率
vol = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, cal, 0.30, dc))
process = ql.BlackScholesMertonProcess(spot, qTS, rTS, vol)

exercise = ql.AmericanExercise(today, today + ql.Period(5, ql.Years))        # 存续期内可转股
sched = ql.Schedule(today, today + ql.Period(5, ql.Years), ql.Period(ql.Annual), cal,
                    ql.Unadjusted, ql.Unadjusted, ql.DateGeneration.Backward, False)
bond = ql.ConvertibleFixedCouponBond(exercise, 10.0, ql.CallabilitySchedule(),
                                     today, 0, [0.015], dc, sched, 100.0)
for cs in (0.0, 0.02, 0.04):
    bond.setPricingEngine(ql.BinomialConvertibleEngine(
        process, "crr", 200, ql.QuoteHandle(ql.SimpleQuote(cs)), ql.DividendSchedule()))
    print(f"信用利差 {cs:.0%}: NPV = {bond.NPV():.3f}")
# 信用利差 0%: NPV = 111.444
# 信用利差 2%: NPV = 104.931   ← 第10章：≈ 104.9
# 信用利差 4%: NPV = 98.863
```

树类型字符串可取 `"crr"`、`"jr"`、`"eqp"`、`"trigeorgis"`、`"tian"`、`"lr"`、`"j4"`。信用利差为0时 QuantLib 得 111.444，与 `fi.convertible`（200步）的 111.978 接近；信用利差为2%时降至 104.931，即第10章"≈104.9 vs ≈112"的来源。

---

## B.8 利率期权与信用

### B.8.1 Cap/Floor 与 BlackCapFloorEngine

`ql.Cap(浮动腿, [执行价])` 与 `ql.Floor(浮动腿, [执行价])` 的浮动腿用 `ql.IborLeg([名义本金], 日程, 指数)` 生成；`ql.BlackCapFloorEngine(折现曲线句柄, 波动率句柄, 计息惯例)` 用 Black 公式逐期定价。

```python
import math
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
cal = ql.NullCalendar()
for dc in (ql.Actual365Fixed(), ql.Thirty360(ql.Thirty360.BondBasis)):
    ts = ql.YieldTermStructureHandle(ql.FlatForward(today, math.log(1.03), dc, ql.Continuous))
    idx = ql.IborIndex("Idx", ql.Period(1, ql.Years), 0, ql.CNYCurrency(), cal,
                       ql.Unadjusted, False, dc, ts)
    sched = ql.Schedule(today, today + ql.Period(5, ql.Years), ql.Period(1, ql.Years), cal,
                        ql.Unadjusted, ql.Unadjusted, ql.DateGeneration.Forward, False)
    cap = ql.Cap(ql.IborLeg([1e8], sched, idx), [0.03])
    cap.setPricingEngine(ql.BlackCapFloorEngine(ts, ql.QuoteHandle(ql.SimpleQuote(0.20)), dc))
    print(dc.name(), f"{cap.NPV():,.0f}", [round(p) for p in cap.optionletsPrice()])
# Actual/365 (Fixed) 1,311,843 [0, 225910, 308943, 366663, 410326]
# 30/360 (Bond Basis) 1,310,756 [0, 225249, 308758, 366527, 410221]
```

第一行即第13章的 1,311,843 元；改用 30/360 后与例13.2 的 1,310,756 元完全一致，第2个 caplet 的 225,249 元即例13.1。`optionletsPrice()` 给出逐期 caplet 价值，首期在估值日已定盘、内在价值为零。`cap.impliedVolatility(价格, 曲线句柄, 初值)` 可由价格反求波动率（例13.4 的对应做法）。

### B.8.2 Swaption 与 BlackSwaptionEngine

正文第13章用 `fi.rateopt.black_swaption` 计算例13.3，未给出 QuantLib 版本。对应写法如下：标的互换用 `VanillaSwap` 构造，行权方式为 `ql.EuropeanExercise(到期日)`。

```python
import QuantLib as ql

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
dc, cal = ql.Thirty360(ql.Thirty360.BondBasis), ql.NullCalendar()
ts = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.03, dc, ql.Compounded, ql.Annual))
idx = ql.IborIndex("Idx", ql.Period(1, ql.Years), 0, ql.CNYCurrency(), cal,
                   ql.Unadjusted, False, dc, ts)
start = today + ql.Period(1, ql.Years)                          # 1 年后行权
sched = ql.Schedule(start, start + ql.Period(4, ql.Years), ql.Period(1, ql.Years), cal,
                    ql.Unadjusted, ql.Unadjusted, ql.DateGeneration.Forward, False)
underlying = ql.VanillaSwap(ql.VanillaSwap.Payer, 1e8, sched, 0.03, dc, sched, idx, 0.0, dc)
swaption = ql.Swaption(underlying, ql.EuropeanExercise(start))
swaption.setPricingEngine(ql.BlackSwaptionEngine(ts, ql.QuoteHandle(ql.SimpleQuote(0.20)), dc))
swaption.NPV()       # 862,392，与例13.3 一致
```

若把计息惯例改为 Actual365Fixed，结果为 863,002 元，差异同样来自闰年。`ql.Swaption(标的互换, 行权方式[, 结算类型, 结算方法])` 默认实物交割。

### B.8.3 FlatHazardRate 与生存概率

```python
import QuantLib as ql
from fi import credit as cr

today = ql.Date(15, 6, 2026); ql.Settings.instance().evaluationDate = today
lam = cr.hazard_from_spread(0.02, 0.4)                     # 0.033333，例14.2
dpts = ql.FlatHazardRate(today, ql.QuoteHandle(ql.SimpleQuote(lam)), ql.Actual365Fixed())
d5 = today + ql.Period(5, ql.Years)
dpts.survivalProbability(d5)        # 0.846404，按 1826/365 年计
dpts.survivalProbability(5.0)       # 0.846482，按整 5 年计
cr.survival_probability(lam, 5)     # 0.846482
dpts.defaultProbability(d5)         # 0.153596
dpts.defaultProbability(today + ql.Period(1, ql.Years), d5)   # 第 1～5 年间的违约概率
```

`FlatHazardRate(参考日, 违约强度句柄, 计息惯例)` 是常数强度的违约期限结构，`survivalProbability`、`defaultProbability`、`hazardRate`、`defaultDensity` 均可按日期或年数取值。按日期取值时，5年区间含2028-02-29，年化分数为 5.00274，生存概率比整5年略低；按年数 `5.0` 取值则与 `fi.credit` 完全一致。由多个期限的 CDS 报价 bootstrap 分段强度曲线，可用 `PiecewiseFlatHazardRate` 与 CDS helper（第14章习题9）。

---

## B.9 常见差异来源与排查清单

全书各章的对拍经验可归纳为下面的排查顺序。对拍出现差异时，宜逐项统一条件、每次只改一项，观察差异如何变化。

1. **估值日**：是否显式设置 `evaluationDate`；未设置时取运行当天日期。曲线若以固定参考日构造（`FlatForward(today, ...)`），修改估值日不会移动曲线；以结算天数构造（`FlatForward(0, cal, ...)`）则随之移动（B.1）。
2. **复利方式**：`FlatForward` 省略复利方式时为连续复利。这是第12章互换（NPV 2,496,143 vs 2,289,854 元，主因）、第13章 Cap（已在代码中以 `log(1.03)` 统一）、第8章浮息债（99.9945 vs 100）差异的首要来源。
3. **计息惯例及子约定**：ACT/ACT 分 ISDA 与 ISMA，30/360 分 BondBasis、USA、European（B.3）。ISDA 下跨闰年的付息期票息不等（第4章）；ISMA 单独调用须给参考期。
4. **闰年与年化分数**：Actual365Fixed 下跨2028年2月29日的区间 $\tau=366/365$，第12章剩余1,260元、第13章 Cap 的1,087元、第14章生存概率第四位小数的差异均源于此；改为 30/360 或按年数取值即可消除。
5. **结算日**：`FixedRateBond` 的第一个参数是结算天数。T+1 时净价在结算日计算，与估值日净价相差可达 $10^{-4}$～$10^{-3}$（第3章编程实验8）。`bondYield`、`OAS` 等方法的结算日参数也应与之一致。
6. **日历与营业日调整**：`China(IB)` + `Following` 会把落在周末、假日的付息日顺延，改变付息期天数（第2章：184天变为183天，应计 0.75 变为 0.745902）；复现名义付息日应使用 `NullCalendar` + `Unadjusted`。还应注意 QuantLib 节假日表只录入至已公布年份（B.2.2）。
7. **首期定盘**：浮动腿首期在估值日定盘时，QuantLib 默认用预测曲线投影；已知定盘值应以 `addFixing` 录入（B.6.2）。第13章首期 caplet 因此内在价值为零，`fi` 的对应示例则从第1年开始计 caplet。
8. **净价与全价**：`cleanPrice` 与 `dirtyPrice`、`BondPrice.Clean` 与 `BondPrice.Dirty` 要与报价口径对应；估值日恰为付息日时两者相等，容易掩盖口径错误，应另取一个付息期中间的日期检验。
9. **插值方式**：分段曲线在节点处一致，节点之间取决于插值对象与方法（B.4.4）。
10. **模型与参数含义**：Hull–White 的 `sigma` 与 `fi.tree` 的对数波动参数含义不同（第9章）；可转债引擎含信用利差而 `fi.convertible` 不含（第10章）。这类差异属于模型差异，不能靠统一惯例消除。
11. **版本差异**：类的构造签名会随版本变化（如可转债，B.7.2），数值也可能因网格与算法细节改变。记录对拍结果时应注明 `ql.__version__`。

各章对拍差异的结论汇总如下：

| 章 | 对拍对象 | QuantLib | `fi` | 差异的主要来源 |
|---|---|---|---|---|
| 第2章 | 应计利息 | 0.75 | 0.75 | 规则付息期内一致；`China(IB)` + `Following` 时为 0.745902 |
| 第3章 | 净价（$y=4\%$） | 97.2249 | 97.2249 | 一致；ISDA 跨闰年票息带来约 $3\times10^{-6}$ 的差异 |
| 第4章 | YTM | 4.0000% | 4.0000% | 同上 |
| 第5章 | 3年即期 | 2.8133% | 2.8132% | 节点处一致；节点间差异来自插值方式 |
| 第6章 | 久期、凸性 | 2.9135 / 2.8286 / 10.877 | 2.9135 / 2.8286 / 10.877 | 差异小于 $10^{-4}$，来自日历与 ISDA |
| 第8章 | 浮息债净价 | 99.9945 | 100.0 | 连续复利为主，季度 $\tau$ 为辅 |
| 第9章 | 可赎回债净价 | 102.69 | 102.91 | 模型不同（Hull–White vs 对数树） |
| 第10章 | 可转债 | 104.93（含2%信用利差） | 111.98 | 信用利差；不含信用利差时为 111.44 |
| 第12章 | 互换 NPV | 2,496,143 | 2,289,854 | 连续复利为主，闰年1,260元 |
| 第13章 | ATM Cap | 1,311,843 | 1,310,756 | 闰年；改为 30/360 后完全一致 |
| 第14章 | 5年生存概率 | 0.846404 | 0.846482 | 按日期计的年化分数含闰日 |

---

## B.10 速查表

| 任务 | 类 / 函数 | 本书章节 |
|---|---|---|
| 设置估值日 | `ql.Settings.instance().evaluationDate = ql.Date(d, m, y)` | 全书 |
| 构造日期、期限 | `ql.Date`、`ql.Period(n, ql.Years)`、`ql.Period("6M")` | 全书 |
| 判断营业日、调整日期 | `ql.China(ql.China.IB)`、`ql.NullCalendar()`、`cal.adjust`、`cal.isBusinessDay` | 第2、3、6章 |
| 生成付息日程 | `ql.Schedule(..., ql.DateGeneration.Backward, False)` | 第2～14章 |
| 计算年化分数 | `ql.ActualActual(ql.ActualActual.ISDA/ISMA)`、`ql.Actual365Fixed()`、`ql.Thirty360(...)` | 第2章 |
| 描述带口径的利率 | `ql.InterestRate(r, dc, ql.Compounded, ql.Annual)` | 第3、4、6章 |
| 平坦曲线 | `ql.FlatForward(today, r, dc[, comp, freq])` | 第8～13章 |
| 节点曲线 | `ql.ZeroCurve`、`ql.DiscountCurve` | 附录 B.4.3 |
| 债券曲线 bootstrap | `ql.FixedRateBondHelper` + `ql.PiecewiseLogLinearDiscount` | 第5章 |
| 互换曲线 bootstrap | `ql.SwapRateHelper` + `ql.PiecewiseLogLinearDiscount` | 第12章（例12.4，本附录 B.4.5） |
| 取远期利率 | `curve.forwardRate(d1, d2, dc, ql.Simple)` | 第11章 |
| 固息债定价 | `ql.FixedRateBond` + `ql.BondFunctions.cleanPrice` 或 `ql.DiscountingBondEngine` | 第3章 |
| 价格求收益率 | `bond.bondYield(ql.BondPrice(p, ql.BondPrice.Clean), dc, comp, freq)` | 第4章 |
| 久期、凸性、BPV | `ql.BondFunctions.duration/convexity/basisPointValue` | 第6、7章 |
| 应计利息 | `bond.accruedAmount(date)`、`ql.BondFunctions.accruedDays` | 第2章 |
| 自定义浮动指数 | `ql.IborIndex(..., ql.CNYCurrency(), ..., handle)` | 第8、12、13章 |
| 浮息债定价 | `ql.FloatingRateBond` + `ql.DiscountingBondEngine` | 第8章 |
| 录入历史定盘 | `idx.addFixing(date, rate)` | 附录 B.6.2 |
| 利率互换 | `ql.VanillaSwap` + `ql.DiscountingSwapEngine`；`NPV`、`fairRate`、`fixedLegBPS` | 第12章 |
| 可赎回/可回售债 | `ql.CallabilitySchedule`、`ql.Callability`、`ql.CallableFixedRateBond` | 第9章 |
| 短利率树与 OAS | `ql.HullWhite` + `ql.TreeCallableFixedRateBondEngine`；`bond.OAS`、`effectiveDuration` | 第9章 |
| 可转债 | `ql.ConvertibleFixedCouponBond` + `ql.BlackScholesMertonProcess` + `ql.BinomialConvertibleEngine` | 第10章 |
| 利率上/下限 | `ql.Cap`/`ql.Floor` + `ql.IborLeg` + `ql.BlackCapFloorEngine` | 第13章 |
| 互换期权 | `ql.Swaption` + `ql.EuropeanExercise` + `ql.BlackSwaptionEngine` | 第13章（本附录 B.8.2） |
| 违约强度与生存概率 | `ql.FlatHazardRate`；`survivalProbability`、`defaultProbability` | 第14章 |
| 情景重估 | `SimpleQuote.setValue` 或 `RelinkableYieldTermStructureHandle.linkTo` 后重新取值 | 第7、18章 |

!!! note "延伸阅读"
    QuantLib 项目主页为 <https://www.quantlib.org>，Python 绑定的源代码与示例见 <https://github.com/lballabio/QuantLib-SWIG>。社区维护的 Python 接口说明可参阅 <https://quantlib-python-docs.readthedocs.io/>，但其内容未必与本机版本同步，签名应以本机实测为准。
