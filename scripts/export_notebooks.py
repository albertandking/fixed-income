"""将 notebook 的代码与输出手动导出为 markdown 片段，供正文引用。

运行：uv run python scripts/export_notebooks.py

骨架占位：随写作流程补全（可基于 nbconvert）。
"""

from __future__ import annotations

from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "notebooks"


def main() -> None:
    print("TODO：导出", len(list(NB.glob("ch*.ipynb"))), "个 notebook 的片段供正文引用")


if __name__ == "__main__":
    main()
