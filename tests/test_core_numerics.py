"""关键数值函数的回归测试：应计利息口径与到期收益率求解的稳健性。"""

import datetime as dt

import pytest

from fi import cashflow as cf
from fi.pricing import price_bond, ytm


def test_accrued_interest_regular_period():
    # 例2.4：同一非闰年内的规则付息期
    ai = cf.accrued_interest(dt.date(2026, 6, 15), dt.date(2026, 3, 15), dt.date(2026, 9, 15),
                             coupon_rate=0.03, freq=2, face=100, convention="ACT/ACT")
    assert ai == pytest.approx(0.75, abs=1e-12)


def test_accrued_interest_leap_year_uses_t_over_ts():
    # 跨闰年付息期：按 t/TS = 92/182 计，与 QuantLib ActualActual(ISMA) 一致
    ai = cf.accrued_interest(dt.date(2028, 2, 15), dt.date(2027, 11, 15), dt.date(2028, 5, 15),
                             coupon_rate=0.03, freq=2, face=100, convention="ACT/ACT")
    assert ai == pytest.approx(1.5 * 92 / 182, abs=1e-12)


def test_accrued_interest_30_360():
    ai = cf.accrued_interest(dt.date(2026, 6, 15), dt.date(2026, 3, 15), dt.date(2026, 9, 15),
                             coupon_rate=0.03, freq=2, face=100, convention="30/360")
    assert ai == pytest.approx(0.75, abs=1e-12)


@pytest.mark.parametrize("price,guess", [(97.2249, 0.03), (5.0, 10.0), (5.0, 0.03),
                                         (200.0, 0.03), (102.0, 0.30)])
def test_ytm_round_trip(price, guess):
    cfs, ts = [3, 103], [1, 2]
    y = ytm(price, cfs, ts, freq=1, guess=guess)
    assert y > -1
    assert price_bond(cfs, ts, y, 1) == pytest.approx(price, abs=1e-8)


def test_ytm_example_4_1():
    assert ytm(97.2249, [3, 3, 103], [1, 2, 3], freq=1) == pytest.approx(0.04, abs=1e-6)


def test_ytm_unreachable_price_raises():
    # 价格远高于现金流可达上限（收益率需低于合法域下界）
    with pytest.raises(ValueError):
        ytm(1e9, [3, 103], [1, 2], freq=1, guess=10.0)
    with pytest.raises(ValueError):
        ytm(-1.0, [3, 103], [1, 2], freq=1)
