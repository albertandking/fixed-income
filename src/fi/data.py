"""数据读取与内置离线样本加载。

约定：
- 内置示例数据放在 ``data/processed/``（入库，离线可跑）。
- 联网抓取的真实数据由 ``scripts/fetch_data.py`` 写入 ``data/raw/``（不入库）。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# 仓库根目录下的 data/processed
_PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"


def processed_dir() -> Path:
    """返回内置示例数据目录。"""
    return _PROCESSED


def load_sample(name: str) -> pd.DataFrame:
    """加载一份内置离线样本数据集。

    Parameters
    ----------
    name : str
        文件名（不含扩展名），如 ``"cgb_yield_curve"``。

    Returns
    -------
    pandas.DataFrame
    """
    for ext, reader in ((".parquet", pd.read_parquet), (".csv", pd.read_csv)):
        path = _PROCESSED / f"{name}{ext}"
        if path.exists():
            return reader(path)
    raise FileNotFoundError(
        f"未找到内置样本 {name!r}；请先运行 `uv run python scripts/make_sample_data.py`。"
    )
