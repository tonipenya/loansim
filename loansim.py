from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Tuple

import pandas as pd
from dateutil.relativedelta import relativedelta
from scipy.stats import gaussian_kde


@dataclass
class Amortization:
    date: date
    amount: float
    interest_payed: float
    outstanding_payed: float
    outstanding: float


@dataclass(order=True)
class Payment:
    date: (
        date | None
    )  # keep date as first field (field order determines results of comparisons for sorting)
    amount: float = 0

    def __add__(self, other: "Payment") -> "Payment":
        if not isinstance(other, self.__class__):
            raise TypeError("Must be same class")

        return Payment(
            self.date if self.date == other.date else None, self.amount + other.amount
        )

    def __radd__(self, value: int) -> "Payment":
        # To enable using sum([Payment, Payment]) https://stackoverflow.com/a/1218735
        return Payment(self.date, self.amount + value)


class PaymentSchema(Iterable):
    def for_date(self, date: date) -> Payment:
        raise NotImplementedError


class PastOverpayments(PaymentSchema):
    def __init__(self, past_overpayments_path: str) -> None:
        self.overpayments: dict[date, Payment] = {
            payment["date"].date(): Payment(payment["date"].date(), payment["amount"])
            for payment in pd.read_csv(
                past_overpayments_path, parse_dates=["date"]
            ).to_dict("records")
        }

    def for_date(self, date: date) -> Payment:
        if date not in self.overpayments:
            return Payment(date, 0.0)
        return self.overpayments[date]

    def __iter__(self):
        return sorted(self.overpayments.values()).__iter__()


@dataclass
class PaymentsInRange(PaymentSchema):
    start_date: date
    end_date: date | None
    amount: float

    def for_date(self, date: date) -> Payment:
        if (
            (self.start_date and date < self.start_date)
            or (self.end_date and date > self.end_date)
            or date.day != 1
        ):
            return Payment(date, 0.0)

        return Payment(date, self.amount)

    def __iter__(self):
        return (
            Payment(self.start_date + relativedelta(months=month_count), self.amount)
            for month_count in range(months_diff(self.start_date, self.end_date) + 1)
        )


def kde(payments: PaymentSchema) -> pd.Series:
    values = pd.DataFrame(payments).set_index("date").amount
    values = values[values != 0]
    min_index = int(values.min())
    max_index = int(values.max())
    index_step = max(min(max_index // 10_000, len(values)), 1)

    ind = pd.RangeIndex(min_index, max_index, index_step)
    gkde = gaussian_kde(values)
    return pd.Series(data=gkde.evaluate(ind), index=ind)


def months_diff(first_date, last_date) -> int:
    delta = relativedelta(last_date, first_date)
    return (delta.years * 12) + delta.months


def outstanding(
    first_date: date,
    outstanding_date: date,
    interest_rate: float,
    mortgage_amount: float,
    payment_schemas: list[PaymentSchema],
) -> float:
    # `*_, x = Xs` gets the assigns the last value of iterator `Xs` to `x``
    *_, last_amortization_data = simulate(
        first_date=first_date,
        last_date=outstanding_date,
        interest_rate=interest_rate,
        outstanding=mortgage_amount,
        payment_schemas=payment_schemas,
    )

    return last_amortization_data.outstanding


def payments_per_year(payments: PaymentSchema) -> pd.Series:
    yearly_overpayment = pd.DataFrame(payments)
    yearly_overpayment["date"] = pd.to_datetime(yearly_overpayment.date)
    return yearly_overpayment.groupby(yearly_overpayment.date.dt.year).amount.sum()


def payment_table(
    first_date: date,
    interest_rate: float,
    outstanding: float,
    payments: list[PaymentSchema],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            simulation
            for simulation in simulate(
                first_date=first_date,
                interest_rate=interest_rate,
                outstanding=outstanding,
                payment_schemas=payments,
            )
        ]
    ).set_index("date")


def simulate(
    first_date: date,
    interest_rate: float,
    outstanding: float,
    last_date: date | None = None,
    payment_schemas: list[PaymentSchema] = [],
):
    payment_date = first_date

    while outstanding > 0 and (last_date is None or payment_date < last_date):
        payment = sum(
            schema.for_date(payment_date) for schema in payment_schemas
        ) or Payment(None)
        interest_payed = outstanding * interest_rate / 12
        outstanding_payed = payment.amount - interest_payed
        outstanding = outstanding - outstanding_payed

        yield Amortization(
            date=payment_date,
            amount=payment.amount,
            interest_payed=interest_payed,
            outstanding_payed=outstanding_payed,
            outstanding=outstanding,
        )

        payment_date = payment_date + relativedelta(months=1)


def stats(payments: PaymentSchema) -> Tuple[float, float, float, float]:
    s = (
        pd.DataFrame(payments)
        .set_index("date")
        .reindex(
            pd.date_range(
                min(payments).date,
                max(payments).date,
                freq="MS",
                inclusive="both",
            ).date,
            method="nearest",
            fill_value=0,
            tolerance=timedelta(days=3),  # type: ignore[arg-type]
        )
        .amount
    )
    return s.quantile(0.25), s.quantile(0.75), s.mean(), s.median()
