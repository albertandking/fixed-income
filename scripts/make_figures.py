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

from fi import curve as fc  # noqa: E402
from fi import data, frn, plotting, risk, tree  # noqa: E402
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
    ax.plot(curve["tenor"], curve["yield_pct"], marker="o", label="即期利率 z(t)（样本近似）")
    ax.plot(fwd_x, fwd_y, marker="s", ls="--", label="隐含远期利率 f")
    ax.set_xlabel("期限（年）"); ax.set_ylabel("利率 (%)")
    ax.set_title("图4-1　即期曲线与隐含远期曲线"); ax.legend()
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


# --- 第9章 ---------------------------------------------------------------

def ch09_frn_vs_fixed() -> None:
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
    ax.set_title("图9-1　浮息债 vs 固息债：利率变动下的价格稳定性"); ax.legend()
    _save(fig, "ch09_frn_vs_fixed.png")


# --- 第10章 --------------------------------------------------------------

def ch10_callable() -> None:
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
    ax.set_title("图10-1　可赎回债的负凸性：低利率端价格被赎回价封顶"); ax.legend()
    _save(fig, "ch10_callable.png")


# --- 第8章 ---------------------------------------------------------------

def _money_market():
    mm = data.load_sample("money_market").copy()
    mm["date"] = mm["date"].astype("datetime64[ns]")
    return mm.set_index("date")


def ch08_carry() -> None:
    mm = _money_market()
    carry = mm["cgb_10y"] - mm["dr007"]
    r_dr = mm["r007"] - mm["dr007"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6))
    ax1.plot(carry.index, carry.values)
    ax1.set_ylabel("carry (%)"); ax1.set_title("图8-1　carry = 10Y 国债收益率 − DR007")
    ax2.plot(r_dr.index, r_dr.values, color="C3")
    ax2.set_ylabel("R007 − DR007 (%)"); ax2.set_title("图8-3　非银流动性分层利差")
    _save(fig, "ch08_carry.png")


def ch08_leverage_nav() -> None:
    mm = _money_market()
    y_d, r_d = mm["cgb_10y"] / 100, mm["dr007"] / 100

    def daily(L):
        return (y_d + (L - 1) * (y_d - r_d)) / 250

    cum1 = (1 + daily(1)).cumprod()
    cum3 = (1 + daily(3)).cumprod()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(cum1.index, cum1.values, label="L=1（不加杠杆）")
    ax.plot(cum3.index, cum3.values, label="L=3")
    ax.set_ylabel("累计净值"); ax.set_title("图8-2　杠杆前后累计回报对比"); ax.legend()
    _save(fig, "ch08_leverage_nav.png")


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
    ch09_frn_vs_fixed()
    ch10_callable()
    ch08_carry()
    ch08_leverage_nav()
    print("所有图已生成至", FIG)


if __name__ == "__main__":
    main()
