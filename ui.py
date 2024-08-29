import json
from datetime import date

import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta

from loansim import (
    CompositePayments,
    PastOverpayments,
    PaymentsInRange,
    kde,
    outstanding,
    payment_table,
    payments_per_year,
    stats,
)

INITIAL_CONDITIONS_FILE = "./data/initial_conditions.json"
PAST_OVERPAYMENTS_FILE = "./data/past_overpayments.csv"
initial_conditions = json.load(open(INITIAL_CONDITIONS_FILE))
START_DATE = date.fromisoformat(initial_conditions["start_date"])
MORTGAGE_AMOUNT = initial_conditions["mortgage_amount"]
INTEREST_RATE = initial_conditions["interest_rate"]
MONTHLY_PAYMENT = initial_conditions["monthly_payment"]

past_overpayments = PastOverpayments(PAST_OVERPAYMENTS_FILE)
all_monthly_installments = PaymentsInRange(
    start_date=START_DATE, end_date=None, amount=MONTHLY_PAYMENT
)
p25_overpayment, p75_overpayment, mean_overpayment, median_overpayment = stats(
    past_overpayments
)
overpayment_amounts_for_simulations = sorted(
    [
        int(n)
        for n in [
            0,
            p25_overpayment,
            mean_overpayment,
            median_overpayment,
            p75_overpayment,
        ]
    ]
)
simulations = {
    amount: payment_table(
        outstanding=MORTGAGE_AMOUNT,
        first_date=START_DATE,
        interest_rate=INTEREST_RATE,
        payments=CompositePayments(
            [
                all_monthly_installments,
                past_overpayments,
                PaymentsInRange(  # Future overpayments
                    start_date=date.today(),
                    end_date=None,
                    amount=amount,
                ),
            ],
        ),
    )
    for amount in overpayment_amounts_for_simulations
}


st.set_page_config(layout="wide")
st.title("Loan simulator")


st.header("Summary")
col1, col2 = st.columns(2)

with col1:
    monthly_installments_to_date = PaymentsInRange(
        start_date=START_DATE, end_date=date.today(), amount=MONTHLY_PAYMENT
    )
    current_outstanding = outstanding(
        first_date=START_DATE,
        outstanding_date=date.today(),
        interest_rate=INTEREST_RATE,
        mortgage_amount=MORTGAGE_AMOUNT,
        payments=CompositePayments([monthly_installments_to_date, past_overpayments]),
    )
    time_since_loan_start = relativedelta(date.today(), START_DATE)
    st.write(f"**Outstanding:**  {current_outstanding:,.2f} €")
    st.write(f"**Amortized:** {(MORTGAGE_AMOUNT - current_outstanding):,.2f} €")
    st.write(
        f"**Loan start date:** {START_DATE} ({time_since_loan_start.years} years and {time_since_loan_start.months} months ago)"
    )

with col2:
    df = pd.DataFrame(
        {
            "monthly overpayment": amount,
            "last payment": (
                last_payment_date := simulation.outstanding[
                    simulation.outstanding <= 0
                ].index[0]
            ),
            "remaining time": f"{relativedelta(last_payment_date, date.today()).years} years"
            f" and {relativedelta(last_payment_date, date.today()).months} months",
        }
        for amount, simulation in simulations.items()
    )
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={"amount": st.column_config.NumberColumn(format="$%.0f €")},
    )


st.header("Overpayments")
[col1, col2, col3] = st.columns(3)

with col1:
    st.subheader("Overpayments for year")
    st.bar_chart(payments_per_year(past_overpayments))

with col2:
    st.subheader("Overpayments made")
    st.bar_chart(past_overpayments, x="date_", y="amount")

with col3:
    st.subheader("Overpayment distribution")
    st.line_chart(kde(past_overpayments))

st.write(
    f"Average overpayment (mean, median): "
    f"{mean_overpayment:.2f}, {median_overpayment:.2f}"
)


st.header("Amortization simulations")
st.line_chart(
    pd.concat(
        (
            simulation.outstanding.rename(amount)
            for amount, simulation in simulations.items()
        ),
        axis=1,
    ),
    y_label="outstanding",
)
