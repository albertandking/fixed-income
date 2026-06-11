"""由 notebook/复用包生成正文静态图，写入 book/assets/figures/（PNG）。

运行：uv run python scripts/make_figures.py

骨架占位：随各章撰写补全。
"""

from __future__ import annotations

from pathlib import Path

FIG = Path(__file__).resolve().parents[1] / "book" / "assets" / "figures"


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    print("TODO：生成各章正文图至", FIG)


if __name__ == "__main__":
    main()
