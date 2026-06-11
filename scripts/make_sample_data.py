"""离线生成内置示例数据集，写入 data/processed/（入库，保证断网可跑）。

运行：uv run python scripts/make_sample_data.py

骨架占位：随各章撰写补全具体数据集。当前先生成一个最小的国债收益率曲线样例，
保证 fi.data.load_sample("cgb_yield_curve") 可用。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


def make_cgb_yield_curve() -> pd.DataFrame:
    """一条示意性的国债到期收益率曲线（仅作骨架占位，非真实行情）。"""
    tenors = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 30]
    yields = [1.55, 1.62, 1.75, 1.95, 2.08, 2.25, 2.40, 2.55, 2.90]
    return pd.DataFrame({"tenor": tenors, "yield_pct": yields})


def make_money_market(n: int = 250) -> pd.DataFrame:
    """一年期日度货币市场利率样本（确定性合成，单位 %，非真实行情）。

    含 DR007（存款类机构质押式回购）、R007（全市场）、1 年期同业存单收益率、
    10 年期国债收益率，供第8章回购与套息案例使用。
    """
    t = np.arange(n)
    cyc = 2 * np.pi * t / 250
    dr007 = 1.80 + 0.25 * np.sin(cyc)                       # 资金中枢围绕 1.8% 波动
    r007 = dr007 + 0.15 + 0.12 * np.abs(np.sin(2 * np.pi * t / 40))  # R 高于 DR，且有季节性走高
    ncd_1y = 1.95 + 0.20 * np.sin(cyc + 0.5)
    cgb_10y = 2.55 + 0.15 * np.sin(cyc - 0.3)
    dates = pd.bdate_range("2025-01-02", periods=n)
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "dr007": dr007.round(4),
        "r007": r007.round(4),
        "ncd_1y": ncd_1y.round(4),
        "cgb_10y": cgb_10y.round(4),
    })


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    datasets = {
        "cgb_yield_curve": make_cgb_yield_curve(),
        "money_market": make_money_market(),
    }
    for name, df in datasets.items():
        out = PROCESSED / f"{name}.csv"
        df.to_csv(out, index=False)
        print(f"已生成 {out}（{len(df)} 行）")


if __name__ == "__main__":
    main()
