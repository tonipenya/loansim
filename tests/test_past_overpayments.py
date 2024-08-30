from datetime import date

import pytest

from loansim import PastOverpayments, Payment


def test_access_by_index_returns_payment():
    po = PastOverpayments("./tests/overpayments.csv")

    assert Payment(date(2020, 3, 1), 2_000) == po[1]


def test_access_by_date_returns_Payment():
    po = PastOverpayments("./tests/overpayments.csv")

    assert Payment(date(2020, 5, 1), 3_000) == po[date(2020, 5, 1)]


def test_error_raised_when_accessing_beyond_last_value():
    po = PastOverpayments("./tests/overpayments.csv")

    with pytest.raises(IndexError):
        po[3]
