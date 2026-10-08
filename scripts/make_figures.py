"""由复用包生成正文静态图，写入 book/assets/figures/（PNG，入库供 MkDocs 引用）。

运行：uv run python scripts/make_figures.py

图与各章 notebook 同源，保证正文图与可运行代码一致。需在装好中文字体的机器上生成
（plotting.use_chinese_style 已配置常见 CJK 字体），生成的 PNG 提交入库，CI 直接引用。
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from fi import backtest as bt  # noqa: E402
from fi import convertible as cb  # noqa: E402
from fi import credit as cr  # noqa: E402
from fi import curve as fc  # noqa: E402
from fi import securitization as sz  # noqa: E402
from fi import data, frn, futures, plotting, rateopt, risk, swap, tree  # noqa: E402
from fi import var as fivar  # noqa: E402
from fi.cashflow import make_cashflows  # noqa: E402
from fi.pricing import price_bond, forward_rate  # noqa: E402

FIG = Path(__file__).resolve().parents[1] / "book" / "assets" / "figures"


def _save(fig, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# --- 第1章 ---------------------------------------------------------------

def ch01_yield_curve() -> None:
    curve = data.load_sample("cgb_yield_curve")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(curve["tenor"], curve["yield_pct"], marker="o")
    ax.set_xlabel("期限（年）"); ax.set_ylabel("到期收益率 (%)")
    ax.set_title("图1-1　中国国债收益率曲线（样本数据）")
    _save(fig, "ch01_yield_curve.png")


# --- 第2章 ---------------------------------------------------------------

def ch02_mortgage() -> None:
    from fi import cashflow as cf
    P, rate, k, N = 1_000_000, 0.05, 12, 360
    i = rate / k
    pmt = cf.annuity_payment(P, rate, N, freq=k)
    bal, eq_int, eq_prin = P, [], []
    for _ in range(N):
        interest = bal * i
        eq_int.append(interest); eq_prin.append(pmt - interest); bal -= pmt - interest
    bal2, ep_pay = P, []
    fixed = P / N
    for _ in range(N):
        ep_pay.append(fixed + bal2 * i); bal2 -= fixed
    m = np.arange(1, N + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    ax1.stackplot(m, eq_prin, eq_int, labels=["本金", "利息"])
    ax1.set_title("图2-1　等额本息月供构成"); ax1.set_xlabel("月"); ax1.legend(loc="upper right")
    ax2.plot(m, [pmt] * N, label="等额本息")
    ax2.plot(m, ep_pay, label="等额本金")
    ax2.set_title("两种还款方式月供对比"); ax2.set_xlabel("月"); ax2.legend()
    _save(fig, "ch02_mortgage.png")


# --- 第3章 ---------------------------------------------------------------

def ch03_price_yield() -> None:
    cfs, ts = make_cashflows(0.03, 3, freq=1, face=100)
    ys = np.linspace(0.0, 0.08, 161)
    ps = [price_bond(cfs, ts, y, 1) for y in ys]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ys * 100, ps)
    ax.axhline(100, ls=":", color="gray"); ax.axvline(3, ls=":", color="gray")
    ax.set_xlabel("到期收益率 y (%)"); ax.set_ylabel("价格")
    ax.set_title("图3-1　价格—收益率关系（票息 3%，y=3% 时平价）")
    _save(fig, "ch03_price_yield.png")


def ch03_pull_to_par() -> None:
    mats = np.arange(10, 0 - 1e-9, -1)

    def price_at(coupon, y, mat):
        if mat <= 0:
            return 100.0
        cf, t = make_cashflows(coupon, mat, freq=1, face=100)
        return price_bond(cf, t, y, 1)

    prem = [price_at(0.04, 0.025, m) for m in mats]
    disc = [price_at(0.015, 0.025, m) for m in mats]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(mats, prem, label="溢价债（票息4%, y=2.5%）")
    ax.plot(mats, disc, label="折价债（票息1.5%, y=2.5%）")
    ax.axhline(100, ls=":", color="gray")
    ax.set_xlabel("剩余期限（年）"); ax.set_ylabel("价格"); ax.invert_xaxis()
    ax.set_title("图3-2　拉回面值：到期临近，价格收敛到 100"); ax.legend()
    _save(fig, "ch03_pull_to_par.png")


# --- 第4章 ---------------------------------------------------------------

def ch04_spot_forward() -> None:
    curve = data.load_sample("cgb_yield_curve")
    zt = dict(zip(curve["tenor"], curve["yield_pct"] / 100))
    ten = list(curve["tenor"])
    fwd_x, fwd_y = [], []
    for a, b in zip(ten[:-1], ten[1:]):
        fwd_x.append(b)
        fwd_y.append(forward_rate(lambda t: zt[t], a, b, freq=1) * 100)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(curve["tenor"], curve["yield_pct"], marker="o", label="即期利率 z(t)（教学样本）")
    ax.plot(fwd_x, fwd_y, marker="s", ls="--", label="相邻区间远期利率 f（画在区间右端）")
    ax.set_xlabel("期限（年）"); ax.set_ylabel("利率 (%)")
    ax.set_title("图4-1　教学样本即期曲线与相邻区间远期利率"); ax.legend()
    _save(fig, "ch04_spot_forward.png")


# --- 第5章 ---------------------------------------------------------------

def ch05_three_curves() -> None:
    cv = data.load_sample("cgb_yield_curve")
    ten = np.arange(1, 11)
    par = fc.interpolate(cv["tenor"], cv["yield_pct"] / 100, ten, "linear")
    zeros, _ = fc.bootstrap(par)
    fwd_t, fwd = fc.forward_curve(zeros)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ten, par * 100, marker="o", label="到期收益率（平价）")
    ax.plot(ten, zeros * 100, marker="^", label="即期利率（bootstrap）")
    ax.plot(fwd_t, fwd * 100, marker="s", ls="--", label="远期利率")
    ax.set_xlabel("期限（年）"); ax.set_ylabel("利率 (%)")
    ax.set_title("图5-1　到期 / 即期 / 远期三条曲线（par < spot < forward）"); ax.legend()
    _save(fig, "ch05_three_curves.png")


# --- 第6章 ---------------------------------------------------------------

def ch06_price_yield_tangent() -> None:
    cfs, ts = make_cashflows(0.03, 3, freq=1, face=100)
    y = 0.03
    P = price_bond(cfs, ts, y, 1)
    d_mod = risk.modified_duration(cfs, ts, y, 1)
    ys = np.linspace(0.0, 0.06, 121)
    prices = [price_bond(cfs, ts, yi, 1) for yi in ys]
    tangent = [P * (1 - d_mod * (yi - y)) for yi in ys]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(ys * 100, prices, label="真实价格 P(y)")
    ax.plot(ys * 100, tangent, "--", label="久期切线（一阶近似）")
    ax.scatter([y * 100], [P], color="k", zorder=5)
    ax.set_xlabel("到期收益率 y (%)"); ax.set_ylabel("价格")
    ax.set_title("图6-1　价格—收益率曲线与久期切线（凸性使真实价格高于切线）"); ax.legend()
    _save(fig, "ch06_price_yield_tangent.png")


def ch06_krd() -> None:
    curve = data.load_sample("cgb_yield_curve").set_index("tenor")["yield_pct"] / 100
    key_tenors = np.array([2.0, 5.0, 10.0])
    zeros = curve[[2, 5, 10]].to_numpy()
    cf10, t10 = make_cashflows(float(curve[10]), 10, freq=2, face=100)
    krd = risk.key_rate_durations(cf10, t10, key_tenors, zeros)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([f"{int(k)}Y" for k in key_tenors], krd)
    ax.set_ylabel("关键利率久期"); ax.set_title("图6-2　10Y 国债的关键利率久期分布")
    _save(fig, "ch06_krd.png")


# --- 第7章 ---------------------------------------------------------------

def ch07_immunization() -> None:
    cfs, ts = make_cashflows(0.03, 6, freq=1, face=100)
    y0 = 0.03
    P0 = price_bond(cfs, ts, y0, 1)
    H = risk.macaulay_duration(cfs, ts, y0, 1)   # 持有期 = 久期
    target = P0 * (1 + y0) ** H
    dys = np.linspace(-0.02, 0.02, 81)
    vals = [sum(cf * (1 + y0 + dy) ** (H - t) for cf, t in zip(cfs, ts)) for dy in dys]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(dys * 100, vals)
    ax.axhline(target, ls=":", color="gray", label=f"目标终值 {target:.2f}")
    ax.axvline(0, ls=":", color="gray")
    ax.set_xlabel("利率平行移动 Δy (%)"); ax.set_ylabel(f"H={H:.2f}年 时点实现终值")
    ax.set_title("图7-1　单期免疫：久期=持有期时财富被锁定（Δy=0 处最小）"); ax.legend()
    _save(fig, "ch07_immunization.png")


# --- 第8章 ---------------------------------------------------------------

def ch08_frn_vs_fixed() -> None:
    refs = np.linspace(0.01, 0.04, 61)
    # 浮息债：DM=QM=0.5%，2 年季付
    frn_p = [frn.price_frn(L, 0.005, 0.005, n_periods=8, freq=4) for L in refs]
    # 固息债：票息固定 2.5%，2 年季付，收益率 = 市场利率 + 0.5% 利差
    fix_p = []
    for L in refs:
        cf, t = make_cashflows(0.025, 2, freq=4, face=100)
        fix_p.append(price_bond(cf, t, L + 0.005, freq=4))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(refs * 100, frn_p, label="浮息债（DM=QM）")
    ax.plot(refs * 100, fix_p, label="固息债（票息 2.5%）")
    ax.axhline(100, ls=":", color="gray")
    ax.set_xlabel("市场利率 (%)"); ax.set_ylabel("价格")
    ax.set_title("图8-1　浮息债 vs 固息债：利率变动下的价格稳定性"); ax.legend()
    _save(fig, "ch08_frn_vs_fixed.png")


# --- 第9章 --------------------------------------------------------------

def ch09_callable() -> None:
    refs = np.linspace(0.01, 0.08, 36)
    sig, n, cpn = 0.20, 6, 6.0
    straight = [tree.value_bond(tree.short_rate_tree(r, sig, n), cpn, 100) for r in refs]
    callable_ = [tree.value_bond(tree.short_rate_tree(r, sig, n), cpn, 100,
                                 call_price=100, call_from=1) for r in refs]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(refs * 100, straight, label="普通债")
    ax.plot(refs * 100, callable_, label="可赎回债（赎回价 100）")
    ax.axhline(100, ls=":", color="gray")
    ax.set_xlabel("短期利率 r0 (%)"); ax.set_ylabel("价格")
    ax.set_title("图9-1　可赎回债的负凸性：低利率端价格被赎回价封顶"); ax.legend()
    _save(fig, "ch09_callable.png")


# --- 第10章 --------------------------------------------------------------

def ch10_convertible() -> None:
    floor = cb.bond_floor(100, 0.015, 5, discount_rate=0.05)
    ratio = 10
    s = np.linspace(2, 16, 36)
    cv = [cb.price_convertible(si, 0.30, 0.03, 5, 100, 0.015, ratio, n_steps=120)["price"] for si in s]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(s, cv, label="可转债价值", lw=2)
    ax.plot(s, ratio * s, "--", label="转股价值（ratio×S）")
    ax.axhline(floor, ls=":", color="gray", label=f"纯债底 {floor:.1f}")
    ax.set_xlabel("正股价格 S"); ax.set_ylabel("价值")
    ax.set_title("图10-1　可转债的股债性切换"); ax.legend()
    _save(fig, "ch10_convertible.png")


# --- 第14章 --------------------------------------------------------------

def ch14_merton() -> None:
    D, sig, r, T = 100.0, 0.25, 0.03, 1.0
    lev = np.linspace(0.4, 0.92, 40)           # 杠杆 D/V
    V = D / lev
    pd = [cr.merton_pd(v, D, sig, r, T)["pd"] * 100 for v in V]
    spread = [cr.merton_credit_spread(v, D, sig, r, T) * 1e4 for v in V]
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(lev, pd, "C0", label="违约概率 PD")
    ax1.set_xlabel("杠杆 D/V"); ax1.set_ylabel("违约概率 PD (%)", color="C0")
    ax1.tick_params(axis="y", labelcolor="C0")
    ax2 = ax1.twinx()
    ax2.plot(lev, spread, "C3--", label="Merton 信用利差")
    ax2.set_ylabel("信用利差 (bp)", color="C3")
    ax2.tick_params(axis="y", labelcolor="C3")
    ax1.set_title("图14-1　Merton 模型：违约概率与利差随杠杆上升")
    _save(fig, "ch14_merton.png")


# --- 第15章 --------------------------------------------------------------

def ch15_tranching() -> None:
    tranches = [("优先档", 80), ("夹层档", 15), ("次级档", 5)]
    sizes = dict(tranches)
    pool_losses = np.linspace(0, 30, 121)
    series = {n: [] for n, _ in tranches}
    for pl in pool_losses:
        alloc = sz.allocate_losses(pl, tranches)
        for n, _ in tranches:
            series[n].append(alloc[n] / sizes[n] * 100)   # 该档损失率 %
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for n, _ in tranches:
        ax.plot(pool_losses, series[n], label=n)
    ax.set_xlabel("资产池损失率 (%)"); ax.set_ylabel("该档损失率 (%)")
    ax.set_title("图15-1　分层与次级垫底：优先档在池损失突破 20% 前零损失"); ax.legend()
    _save(fig, "ch15_tranching.png")


# --- 第11章 --------------------------------------------------------------

def ch11_hedge() -> None:
    port_dv01 = 50000.0                       # 元/bp（组合市值1亿、久期5）
    ctd_dv01 = futures.bond_dv01(0.032, 8, 0.032)
    ctd_cf = futures.conversion_factor(0.032, 8)
    contract_dv01 = futures.futures_dv01(ctd_dv01, ctd_cf) / 100 * 1e6   # 元/bp 每张
    n = -port_dv01 / contract_dv01            # 套保手数（卖出）
    net_dv01 = port_dv01 + n * contract_dv01  # ≈ 0
    shocks = np.linspace(-100, 100, 41)       # bp
    unhedged = -port_dv01 * shocks / 1e4      # 损益（万元）
    hedged = -net_dv01 * shocks / 1e4
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(shocks, unhedged, label="未对冲组合")
    ax.plot(shocks, hedged, label=f"对冲后（卖出 {abs(round(n))} 张期货）")
    ax.axhline(0, ls=":", color="gray")
    ax.set_xlabel("利率平行冲击 (bp)"); ax.set_ylabel("组合损益（万元）")
    ax.set_title("图11-1　国债期货久期中性套保的效果"); ax.legend()
    _save(fig, "ch11_hedge.png")


# --- 第12章 --------------------------------------------------------------

def ch12_swap_value() -> None:
    taus = [1, 1, 1, 1, 1]
    rates = np.linspace(0.01, 0.05, 41)
    vals = []
    for z in rates:
        dfs = [(1 + z) ** -t for t in range(1, 6)]
        vals.append(swap.swap_value(0.025, dfs, taus, notional=1e8, payer=True) / 1e4)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(rates * 100, vals, label="payer 互换（付固定 2.5%）")
    ax.axhline(0, ls=":", color="gray"); ax.axvline(2.5, ls=":", color="gray")
    ax.set_xlabel("市场利率 (%)"); ax.set_ylabel("互换盯市价值（万元）")
    ax.set_title("图12-1　payer 互换价值随市场利率变动（利率升则获利）"); ax.legend()
    _save(fig, "ch12_swap_value.png")


# --- 第13章 --------------------------------------------------------------

def ch13_capfloor() -> None:
    resets, taus = [1, 2, 3, 4], [1, 1, 1, 1]
    pay_dfs = [1.03 ** -t for t in (2, 3, 4, 5)]
    fwds = [0.03] * 4
    strikes = np.linspace(0.015, 0.045, 31)
    caps = [rateopt.black_cap(fwds, K, 0.20, resets, taus, pay_dfs, kind="cap") / 1e4 for K in strikes]
    floors = [rateopt.black_cap(fwds, K, 0.20, resets, taus, pay_dfs, kind="floor") / 1e4 for K in strikes]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(strikes * 100, caps, label="Cap 价值")
    ax.plot(strikes * 100, floors, label="Floor 价值")
    ax.axvline(3.0, ls=":", color="gray", label="ATM (3%)")
    ax.set_xlabel("执行利率 K (%)"); ax.set_ylabel("价值（万元）")
    ax.set_title("图13-1　Cap 与 Floor 价值随执行价（ATM 处相交）"); ax.legend()
    _save(fig, "ch13_capfloor.png")


# --- 第17章 --------------------------------------------------------------

def ch17_riding() -> None:
    cv = data.load_sample("cgb_yield_curve")
    tenor, yld = cv["tenor"].to_numpy(), (cv["yield_pct"] / 100).to_numpy()
    buy_tenors = [2, 3, 5, 7, 10]
    carries, rolls = [], []
    for bt_ten in buy_tenors:
        yb = float(np.interp(bt_ten, tenor, yld))
        ys = float(np.interp(bt_ten - 1, tenor, yld))
        cf, t = make_cashflows(yb, bt_ten, 1, 100)
        d = risk.modified_duration(cf, t, yb, 1)
        r = bt.riding_attribution(yb, ys, d, yb, 1)
        carries.append(r["carry"] * 100)
        rolls.append(r["rolldown"] * 100)
    x = [f"{b}Y" for b in buy_tenors]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x, carries, label="carry（票息）")
    ax.bar(x, rolls, bottom=carries, label="roll-down（骑乘）")
    ax.set_xlabel("买入期限（持有 1 年）"); ax.set_ylabel("收益贡献 (%)")
    ax.set_title("图17-1　骑乘策略的近似收益分解：carry + roll-down"); ax.legend()
    _save(fig, "ch17_riding.png")


def ch17_riding_stress() -> None:
    """例17.1/例17.3：在曲线不变情景上叠加卖出收益率偏移与合计交易成本。"""
    cv = data.load_sample("cgb_yield_curve")
    tenor, yld = cv["tenor"].to_numpy(), (cv["yield_pct"] / 100).to_numpy()
    buy_tenor, horizon, cost = 5, 1, 0.0010          # 例17.1：买 5 年期持有 1 年；例17.3：成本 0.10%
    yb = float(np.interp(buy_tenor, tenor, yld))               # 2.25%
    ys = float(np.interp(buy_tenor - horizon, tenor, yld))     # 2.165%
    y_short = float(np.interp(horizon, tenor, yld))            # 示意 1 年期点 1.75%
    cf, t = make_cashflows(yb, buy_tenor, 1, 100)
    dur = risk.modified_duration(cf, t, yb, 1)                 # ≈ 4.68
    base = bt.riding_attribution(yb, ys, dur, yb, horizon)["total"]   # ≈ 2.648%

    shift_bp = np.arange(-40, 41)
    gross = (base - dur * shift_bp / 1e4) * 100      # 线性久期近似，未计凸性
    net = gross - cost * 100
    mark_bp = 20
    mark_net = (base - dur * mark_bp / 1e4 - cost) * 100      # ≈ 1.61%

    fig, ax = plt.subplots(figsize=(8, 4.7))
    ax.plot(shift_bp, gross, label="骑乘：未扣成本")
    ax.plot(shift_bp, net, label=f"骑乘：扣除 {cost * 100:.2f}% 成本")
    ax.axhline(y_short * 100, color="C2", ls="--", label=f"示意 1 年期债券：{y_short * 100:.2f}%")
    ax.axvline(0, color="gray", ls=":", lw=1)
    ax.scatter([mark_bp], [mark_net], color="C1", zorder=3)
    ax.annotate(f"+{mark_bp}bp，扣费后约 {mark_net:.2f}%", xy=(mark_bp, mark_net),
                xytext=(-35, mark_net - 0.4),
                arrowprops=dict(arrowstyle="->", color="#555555"))
    ax.set_xlabel(f"卖出时剩余 {buy_tenor - horizon} 年期收益率相对曲线不变情景的偏移（bp）")
    ax.set_ylabel("一年近似收益 (%)")
    ax.set_title("图17-2　利率冲击与骑乘策略近似收益"); ax.legend(loc="upper right")
    _save(fig, "ch17_riding_stress.png")


# --- 第18章 --------------------------------------------------------------

def ch18_var() -> None:
    sigma = fivar.bond_pnl_sigma(1e8, 5, 0.0005)      # 25 万
    rng = np.random.default_rng(7)
    normal = rng.normal(0, sigma, 100000)
    fat = rng.standard_t(4, 100000) * sigma / np.sqrt(4 / 2)   # 厚尾
    var99 = fivar.parametric_var(sigma, 0.99)
    cvar99 = fivar.parametric_cvar(sigma, 0.99)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(normal / 1e4, bins=120, density=True, alpha=0.5, label="正态模拟损益")
    ax.hist(fat / 1e4, bins=200, density=True, alpha=0.4, label="厚尾模拟损益（t 分布，自由度 4）")
    ax.axvline(-var99 / 1e4, color="C3", ls="--", label=f"正态参数法 99% VaR ≈ {var99/1e4:.0f} 万")
    ax.axvline(-cvar99 / 1e4, color="C1", ls=":", label=f"正态参数法 99% ES ≈ {cvar99/1e4:.0f} 万")
    ax.set_xlim(-150, 150)
    ax.set_xlabel("日损益（万元）"); ax.set_ylabel("密度")
    ax.set_title("图18-1　正态与厚尾模拟损益分布及 VaR/ES"); ax.legend()
    _save(fig, "ch18_var.png")


def ch18_factor_scenario() -> None:
    """例18.4：两类债券的基准利率与信用利差分项冲击（线性久期近似，不计凸性）。"""
    gov_value, gov_dur = 60_000_000, 4                # 国债：市值 6000 万元、修正久期 4
    cr_value, cr_dur = 40_000_000, 3                  # 信用债：市值 4000 万元、修正久期 3
    d_rate, d_spread = 0.0050, 0.0080                 # 基准利率 +50bp；信用利差 +80bp
    rate_loss = -(fivar.scenario_pnl(gov_value, gov_dur, 0, d_rate)
                  + fivar.scenario_pnl(cr_value, cr_dur, 0, d_rate)) / 1e4   # 万元，180
    spread_loss = -fivar.scenario_pnl(cr_value, cr_dur, 0, d_spread) / 1e4    # 万元，96
    total = rate_loss + spread_loss                                           # 万元，276

    names = [f"仅基准利率 +{d_rate * 1e4:.0f}bp",
             f"基准利率 +{d_rate * 1e4:.0f}bp\n信用利差 +{d_spread * 1e4:.0f}bp"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(names, [rate_loss, rate_loss], color="C0", label="基准利率冲击损失")
    ax.barh(names, [0, spread_loss], left=[rate_loss, rate_loss], color="C1",
            label="信用利差冲击损失")
    for i in (0, 1):
        ax.text(rate_loss / 2, i, f"{rate_loss:.0f}", ha="center", va="center", color="white")
    ax.text(rate_loss + spread_loss / 2, 1, f"{spread_loss:.0f}", ha="center", va="center",
            color="white")
    ax.text(total + 4, 1, f"合计 {total:.0f}", va="center")
    ax.set_xlim(0, total * 1.2)
    ax.invert_yaxis()
    ax.set_xlabel("近似损失（万元）")
    ax.set_title("图18-2　两类债券的分项情景损益"); ax.legend(loc="upper right")
    _save(fig, "ch18_factor_scenario.png")


# --- 第16章 ---------------------------------------------------------------

def _money_market():
    mm = data.load_sample("money_market").copy()
    mm["date"] = mm["date"].astype("datetime64[ns]")
    return mm.set_index("date")


def ch16_money_market_map() -> None:
    """货币市场工具分类图：按融资方式而非按机构名称分类。"""
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 12); ax.set_ylim(0.75, 7.6); ax.axis("off")

    def box(x, y, w, h, text, color, fontsize=11, linestyle="-"):
        patch = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12",
            linewidth=1.4, edgecolor=color, facecolor=color, alpha=0.13,
            linestyle=linestyle,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fontsize, linespacing=1.45)

    box(4.45, 6.55, 3.1, 0.8, "货币市场\n（通常期限不超过 1 年）", "#1f4e79", 13)
    groups = [
        (0.35, 4.75, "短期债务证券", "#2f75b5"),
        (4.45, 4.75, "存款与银行负债", "#548235"),
        (8.55, 4.75, "机构间资金融通", "#c55a11"),
    ]
    for x, y, title, color in groups:
        box(x, y, 3.1, 0.75, title, color, 12)
        ax.annotate("", xy=(x + 1.55, y + 0.75), xytext=(6, 6.55),
                    arrowprops=dict(arrowstyle="->", color="#777777", lw=1.2))

    box(0.35, 2.55, 3.1, 1.65,
        "政府：短期国库券\n央行：央行票据\n企业：CP / SCP", "#2f75b5")
    box(4.45, 2.55, 3.1, 1.65,
        "同业存单（NCD）\n大额存单（CD）\n短期银行存款", "#548235")
    box(8.55, 2.55, 3.1, 1.65,
        "同业拆借：无担保\n回购：质押式 / 买断式", "#c55a11")
    for x in (1.9, 6.0, 10.1):
        ax.annotate("", xy=(x, 4.2), xytext=(x, 4.75),
                    arrowprops=dict(arrowstyle="->", color="#777777", lw=1.2))

    # 央行公开市场操作属于政策操作，不是机构间融资工具：单列，并用虚线表示它借助回购等交易实施
    box(4.45, 1.0, 3.1, 1.05,
        "央行公开市场操作（政策操作）\n借助逆回购、正回购等交易\n调节银行体系流动性",
        "#7f6000", 10.5, linestyle="--")
    ax.annotate("", xy=(9.2, 2.5), xytext=(7.65, 1.5),
                arrowprops=dict(arrowstyle="->", color="#7f6000", lw=1.2, ls="--"))
    ax.text(9.6, 1.65, "以回购等交易实施", fontsize=9.5, color="#7f6000",
            ha="center", va="center")

    ax.set_title("图16-1　中国货币市场工具分类")
    _save(fig, "ch16_money_market_map.png")


def ch16_repo_rates() -> None:
    """DR007/R007/GC007 的教学情景图，不冒充真实行情。"""
    days = np.arange(1, 31)
    dr = 1.80 + 0.035 * np.sin(days / 3.4)
    nonbank_stress = 0.10 + 0.04 * np.sin(days / 2.8) + 0.55 * np.exp(-((days - 20) / 2.2) ** 2)
    exchange_stress = 0.14 + 0.07 * np.sin(days / 2.1) + 1.05 * np.exp(-((days - 10) / 1.55) ** 2)
    r = dr + nonbank_stress
    gc = dr + exchange_stress

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(days, dr, lw=2.3, label="DR007：银行体系资金中枢")
    ax.plot(days, r, lw=2.0, label="R007：含非银融资溢价")
    ax.plot(days, gc, lw=2.0, label="GC007：交易所资金价格")
    ax.axvspan(8.5, 11.5, color="C2", alpha=0.09)
    ax.axvspan(17.5, 22.5, color="C1", alpha=0.09)
    ax.annotate("交易所资金需求冲击", xy=(10, gc[9]), xytext=(12, 2.82),
                arrowprops=dict(arrowstyle="->", color="C2"), color="C2")
    ax.annotate("非银融资压力上升\nR007 − DR007 走阔", xy=(20, r[19]), xytext=(22.5, 2.65),
                arrowprops=dict(arrowstyle="->", color="C1"), color="C1")
    ax.set_xlabel("交易日（情景序号）"); ax.set_ylabel("7 天期回购利率 (%)")
    ax.set_title("图16-2　DR007、R007 与 GC007 的变化及利差（情景示意，非真实行情）")
    ax.legend(loc="upper left", ncol=1)
    _save(fig, "ch16_repo_rates.png")


def ch16_carry() -> None:
    mm = _money_market()
    carry = mm["cgb_10y"] - mm["dr007"]
    r_dr = mm["r007"] - mm["dr007"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6))
    ax1.plot(carry.index, carry.values)
    ax1.set_ylabel("carry (%)"); ax1.set_title("carry = 10Y 国债收益率 − DR007")
    ax2.plot(r_dr.index, r_dr.values, color="C3")
    ax2.set_ylabel("R007 − DR007 (%)"); ax2.set_title("非银流动性分层利差")
    fig.suptitle("图16-3　套息空间与流动性分层（内置样本数据）")
    fig.tight_layout()
    _save(fig, "ch16_carry.png")


def ch16_leverage_nav() -> None:
    mm = _money_market()
    y_d, r_d = mm["cgb_10y"] / 100, mm["dr007"] / 100

    def daily(L):
        return (y_d + (L - 1) * (y_d - r_d)) / 250

    cum1 = (1 + daily(1)).cumprod()
    cum3 = (1 + daily(3)).cumprod()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(cum1.index, cum1.values, label="L=1（不加杠杆）")
    ax.plot(cum3.index, cum3.values, label="L=3")
    ax.set_ylabel("累计净值"); ax.set_title("图16-4　杠杆前后累计回报对比"); ax.legend()
    _save(fig, "ch16_leverage_nav.png")


def main() -> None:
    plotting.use_chinese_style()
    ch01_yield_curve()
    ch02_mortgage()
    ch03_price_yield()
    ch03_pull_to_par()
    ch04_spot_forward()
    ch05_three_curves()
    ch06_price_yield_tangent()
    ch06_krd()
    ch07_immunization()
    ch08_frn_vs_fixed()
    ch09_callable()
    ch10_convertible()
    ch14_merton()
    ch15_tranching()
    ch11_hedge()
    ch12_swap_value()
    ch13_capfloor()
    ch17_riding()
    ch17_riding_stress()
    ch18_var()
    ch18_factor_scenario()
    ch16_money_market_map()
    ch16_repo_rates()
    ch16_carry()
    ch16_leverage_nav()
    print("所有图已生成至", FIG)


if __name__ == "__main__":
    main()
