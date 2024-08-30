from datetime import date

import pytest

from loansim import Payment, PaymentsInRange


def test_length():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)

    assert 6 == len(pr)


def test_access_by_index_returns_payment():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)

    assert Payment(date(2020, 2, 1), 1_000) == pr[1]


def test_access_by_date_returns_Payment():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)

    assert Payment(date(2020, 5, 1), 1_000) == pr[date(2020, 5, 1)]


def test_error_raised_when_accessing_beyond_last_value():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)

    with pytest.raises(IndexError):
        pr[6]


def test_generates_all_individual_payments():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)
    expected_payments = [
        Payment(date(2020, 1, 1), 1_000),
        Payment(date(2020, 2, 1), 1_000),
        Payment(date(2020, 3, 1), 1_000),
        Payment(date(2020, 4, 1), 1_000),
        Payment(date(2020, 5, 1), 1_000),
        Payment(date(2020, 6, 1), 1_000),
    ]

    assert expected_payments == list(pr)
