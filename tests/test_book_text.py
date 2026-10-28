"""正文与 notebook 的文本完整性检查。

脚本批量编辑时，LaTeX 命令中的 ``\\t``（``\\times``）、``\\a``（``\\approx``）、``\\f``（``\\frac``）
等可能被误转义为控制字符；`mkdocs build --strict` 不会报错，但网页与 Word 版公式会损坏。
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")   # 允许 \t \n \r
FENCE = re.compile(r"^\s*(```|~~~)")

MARKDOWN = sorted((ROOT / "book").rglob("*.md"))
NOTEBOOKS = sorted((ROOT / "notebooks").rglob("*.ipynb"))


@pytest.mark.parametrize("path", MARKDOWN, ids=lambda p: p.name)
def test_markdown_has_no_control_chars(path):
    text = path.read_text(encoding="utf-8")
    assert not CONTROL.search(text)
    fence = False
    for no, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fence = not fence
        elif not fence:
            assert "\t" not in line, f"{path.name}:{no} 正文含制表符（疑为被转义的 \\t…）"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_sources_have_no_control_chars(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    for k, cell in enumerate(nb["cells"]):
        src = "".join(cell["source"])
        assert not CONTROL.search(src), f"{path.name} 第 {k} 个单元含控制字符"
