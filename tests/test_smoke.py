"""冒烟测试：保证复用包可导入、子模块齐全、样例数据可读。"""

import importlib

import pytest

SUBMODULES = [
    "fi.data",
    "fi.cashflow",
    "fi.pricing",
    "fi.curve",
    "fi.risk",
    "fi.repo",
    "fi.credit",
    "fi.backtest",
    "fi.plotting",
]


def test_import_fi():
    fi = importlib.import_module("fi")
    assert fi.__version__


@pytest.mark.parametrize("name", SUBMODULES)
def test_import_submodule(name):
    assert importlib.import_module(name) is not None


def test_load_sample_after_make():
    """若已生成内置样本则应能读取；未生成则跳过（不算失败）。"""
    from fi import data

    try:
        df = data.load_sample("cgb_yield_curve")
    except FileNotFoundError:
        pytest.skip("内置样本未生成；先运行 scripts/make_sample_data.py")
    assert {"tenor", "yield_pct"}.issubset(df.columns)
