"""从中国市场免费接口（akshare/tushare）抓取真实数据，写入 data/raw/（不入库）。

运行：uv run python scripts/fetch_data.py
需要额外依赖：uv sync --extra data

骨架占位：随各章撰写补全具体抓取逻辑。
"""

from __future__ import annotations

from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    print("TODO：用 akshare/tushare 抓取国债收益率、回购利率等并写入", RAW)


if __name__ == "__main__":
    main()
