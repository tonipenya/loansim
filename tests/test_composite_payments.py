from datetime import date

import pytest

from loansim import CompositePayments, PastOverpayments, PaymentsInRange


def test_length_is_addition_of_parts_lengths():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)
    po = PastOverpayments("./tests/overpayments.csv")
    cp = CompositePayments((pr, po))
    assert len(pr) + len(po) == len(cp)


def test_values_around_parts_start_end():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)
    po = PastOverpayments("./tests/overpayments.csv")
    cp = CompositePayments((pr, po))

    assert pr[5] == cp[5]
    assert po[0] == cp[6]
    assert po[2] == cp[8]


def test_error_raised_when_accessing_beyond_last_value():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)
    po = PastOverpayments("./tests/overpayments.csv")
    cp = CompositePayments((pr, po))

    with pytest.raises(IndexError):
        cp[9]


def test_adds_amount_when_accessing_dates_with_multiple_values():
    pr = PaymentsInRange(date(2020, 1, 1), date(2020, 6, 1), 1_000)
    po = PastOverpayments("./tests/overpayments.csv")
    cp = CompositePayments((pr, po))

    assert pr[date(2020, 1, 1)] + po[date(2020, 1, 1)] == cp[date(2020, 1, 1)]
