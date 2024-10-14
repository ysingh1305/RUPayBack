import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
from datetime import timedelta
from dateutil.relativedelta import relativedelta


FPL = 14580 


st.markdown("""
    <style>
    body {
        background-color:#121212;
        color: #f0f0f0;
        font-family: 'Arial', sans-serif;
    }
    .css-1v3fvcr {
        background-color: #121212;
        color: #f0f0f0;
    }
    .stButton button {
        background-color: #e63946;
        color: white;
        border-radius: 10px;
        padding: 10px;
    }
    .stSidebar {
        background-color: #1c1c1c;
    }
    h1, h2, h3, h4 {
        color: #e63946;
    }
    /* Make labels red */
    .stSidebar label {
        color: #e63946 !important;
    }
    /* Make text inside the input fields black */
    .stSidebar input, .stSidebar selectbox, .stSidebar .stNumberInput, .stSidebar textarea, .stSidebar select {
        color: black !important;
        font-size: 16px !important;
    }
    .dataframe {
        background-color: white !important;
        color: black !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


def calculate_idr_payment(agi, fpl):
    discretionary_income = agi - (1.5 * fpl)
    if discretionary_income < 0:
        discretionary_income = 0
    monthly_payment = (0.10 * discretionary_income) / 12
    return max(monthly_payment, 0)


def calculate_repayment(loan_amount, interest_rate, term_years, repayment_type, frequency, agi):
    if repayment_type == 'Income-driven':
        term_years = 20
        monthly_payment = calculate_idr_payment(agi, FPL)

    if frequency == 'Weekly':
        payments_per_year = 52
    elif frequency == 'Bi-weekly':
        payments_per_year = 26
    else:  
        payments_per_year = 12

    payment_intervals = payments_per_year * term_years
    rate_per_period = interest_rate / 100 / payments_per_year
    balance = loan_amount

    if repayment_type == 'Standard':
        payment = npf.pmt(rate_per_period, payment_intervals, -loan_amount)
    elif repayment_type == 'Income-driven':
        payment = monthly_payment
    else:
        payment = npf.pmt(rate_per_period, payment_intervals, -loan_amount)

    payments = []
    total_interest_paid = 0
    accumulated_principal_paid = 0
    accumulated_interest_paid = 0

    for period in range(1, payment_intervals + 1):
        interest_payment = balance * rate_per_period
        principal_payment = payment - interest_payment
        balance -= principal_payment
        total_interest_paid += interest_payment

        accumulated_principal_paid += principal_payment
        accumulated_interest_paid += interest_payment

        payments.append({
            "Period": period,
            "Payment": round(payment, 2),
            "Principal Paid": round(principal_payment, 2),
            "Interest Paid": round(interest_payment, 2),
            "Accumulated Principal Paid": round(accumulated_principal_paid, 2),
            "Accumulated Interest Paid": round(accumulated_interest_paid, 2),
            "Remaining Balance": round(max(balance, 0), 2)
        })

        if balance <= 0:
            break

    return pd.DataFrame(payments), payment, total_interest_paid, period


def calculate_refinanced_loan(loan_amount, new_interest_rate, new_term_years, frequency, repayment_type, agi):
    if repayment_type == 'Income-driven':
        new_term_years = 20
        monthly_payment = calculate_idr_payment(agi, FPL)

    if frequency == 'Weekly':
        payments_per_year = 52
    elif frequency == 'Bi-weekly':
        payments_per_year = 26
    else:
        payments_per_year = 12

    payment_intervals = payments_per_year * new_term_years
    rate_per_period = new_interest_rate / 100 / payments_per_year

    if repayment_type == 'Income-driven':
        payment = monthly_payment
    else:
        payment = npf.pmt(rate_per_period, payment_intervals, -loan_amount)

    refinanced_balances = [loan_amount]
    total_interest_paid = 0
    for period in range(1, payment_intervals + 1):
        interest_payment = refinanced_balances[-1] * rate_per_period
        principal_payment = payment - interest_payment
        total_interest_paid += interest_payment
        refinanced_balances.append(refinanced_balances[-1] - principal_payment)

        if refinanced_balances[-1] <= 0:
            refinanced_balances[-1] = 0
            break

    return payment, total_interest_paid, period, refinanced_balances[:-1]


st.title("💸 RUPAYBACK - Student Loan Repayment Optimizer 💸")


with st.sidebar:
    st.header("Loan Details 💼")
    loan_amount = st.number_input("Loan Amount ($)", value=10000.0, step=1000.0)
    interest_rate = st.number_input("Annual Interest Rate (%)", value=5.0, step=0.1)
    term_years = st.number_input("Loan Term (years)", value=10, step=1)
    agi = st.number_input("Adjusted Gross Income (AGI) ($)", value=50000.0, step=1000.0)
    total_income = st.number_input("Total Income ($)", value=50000.0, step=1000.0)

    st.header("Repayment Options 💡")
    repayment_type = st.selectbox("Repayment Plan", ["Standard", "Income-driven"])
    
    payment_frequency = st.selectbox("Payment Frequency", ["Monthly", "Bi-weekly", "Weekly"])

    loan_start_date = st.date_input("Loan Start Date")


df, payment, total_interest_paid, periods_to_payoff = calculate_repayment(loan_amount, interest_rate, term_years, repayment_type, payment_frequency, agi)

if payment_frequency == 'Weekly':
    loan_end_date = loan_start_date + relativedelta(weeks=+periods_to_payoff)
elif payment_frequency == 'Bi-weekly':
    loan_end_date = loan_start_date + relativedelta(weeks=+2*periods_to_payoff)
else:
    loan_end_date = loan_start_date + relativedelta(months=+periods_to_payoff)

total_loan_cost = loan_amount + total_interest_paid

st.markdown("""
    <div style="background-color:#1e1e1e; padding:15px; border-radius:10px; margin-bottom:20px;">
        <h3 style="color:#e63946;">Loan Repayment Summary</h3>
        <p style="font-size:18px; color:white;">
            💰 <strong>Payment:</strong> <span style="color:#f9c74f;">${:.2f}</span> {}<br>
            📊 <strong>Total Interest Paid:</strong> <span style="color:#f9c74f;">${:.2f}</span><br>
            🕒 <strong>Periods to Payoff:</strong> <span style="color:#f9c74f;">{} {}</span><br>
            📅 <strong>Loan End Date:</strong> <span style="color:#f9c74f;">{}</span><br>
            💵 <strong>Total Loan Cost:</strong> <span style="color:#f9c74f;">${:.2f}</span>
        </p>
    </div>
""".format(payment, payment_frequency.lower(), total_interest_paid, periods_to_payoff, payment_frequency.lower(), loan_end_date.strftime('%B %d, %Y'), total_loan_cost), unsafe_allow_html=True)


if repayment_type == 'Standard':
    st.write("""
    ### Standard Repayment Plan 💼
    - The Standard Repayment Plan involves making fixed monthly payments over a set period (usually 10 years).
    - Your monthly payment amount is determined based on your loan balance and interest rate.
    - This option ensures the loan is paid off in a predictable time frame, usually with the least total interest.
    """)
elif repayment_type == 'Income-driven':
    st.write("""
    ### Income-Driven Repayment Plan 📊
    - The Income-Driven Repayment (IDR) Plan calculates your monthly payments based on your income and family size.
    - Typically, you pay 10% of your discretionary income, and the loan term is extended to 20 years.
    - If any balance remains after 20 years of payments, it may be forgiven.
    - This option can make payments more manageable, especially for borrowers with lower income.
    """)


st.write("#### Repayment Schedule 📅")
st.dataframe(df.style.set_properties(**{
    'background-color': 'white',
    'color': 'black',
    'border': 'none'
}))


st.markdown("---")

df['Debt-to-Income Ratio'] = (df['Remaining Balance'] / total_income) * 100

st.write("#### Debt-to-Income Ratio Over Time 📉")
plt.figure(figsize=(10, 6))
plt.plot(df["Period"], df["Debt-to-Income Ratio"], color='purple', linewidth=2)
plt.xlabel("Period")
plt.ylabel("Debt-to-Income Ratio (%)")
plt.title(f"Debt-to-Income Ratio Over Time ({payment_frequency} Payments)")
plt.xticks(rotation=45)
st.pyplot(plt)

st.write("#### Accumulated Principal, Interest, and Remaining Balance 📉")
plt.figure(figsize=(10, 6))
plt.plot(df["Period"], df["Accumulated Principal Paid"], label='Accumulated Principal Paid', color='blue', linewidth=2)
plt.plot(df["Period"], df["Accumulated Interest Paid"], label='Accumulated Interest Paid', color='orange', linewidth=2)
plt.plot(df["Period"], df["Remaining Balance"], label='Remaining Balance', color='#e63946', linewidth=2)
plt.xlabel("Period")
plt.ylabel("Amount / Balance ($)")
plt.title(f"Accumulated Principal, Interest, and Remaining Balance Over Time ({payment_frequency} Payments)")
plt.xticks(rotation=45)
plt.legend()
st.pyplot(plt)


st.write("#### Breakdown of Total Loan Costs 🍰")
plt.figure(figsize=(8, 8))


total_principal = loan_amount
total_interest = total_interest_paid
labels = ['Principal', 'Interest']
sizes = [total_principal, total_interest]
colors = ['#66b3ff', '#ff9999']


plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)

plt.title("Total Loan Cost Breakdown (Principal vs. Interest)")


st.pyplot(plt)


st.markdown("---")

refinance_checkbox = st.checkbox("Show Refinancing Options")

if refinance_checkbox:
    st.subheader("Refinancing Options 🔄")
    
    new_interest_rate = st.number_input("New Interest Rate (%)", value=3.0, step=0.1)
    new_term_years = st.number_input("New Loan Term (years)", value=10, step=1)

    refinanced_payment, refinanced_total_interest, refinanced_periods, refinanced_balances = calculate_refinanced_loan(loan_amount, new_interest_rate, new_term_years, payment_frequency, repayment_type, agi)

    if payment_frequency == 'Weekly':
        refinanced_loan_end_date = loan_start_date + relativedelta(weeks=+refinanced_periods)
    elif payment_frequency == 'Bi-weekly':
        refinanced_loan_end_date = loan_start_date + relativedelta(weeks=+2*refinanced_periods)
    else:
        refinanced_loan_end_date = loan_start_date + relativedelta(months=+refinanced_periods)

    refinanced_total_loan_cost = loan_amount + refinanced_total_interest

    savings = total_loan_cost - refinanced_total_loan_cost
    if savings > 0:
        savings_message = f"You would save ${savings:.2f} by refinancing."
    else:
        savings_message = f"You would lose ${abs(savings):.2f} by refinancing."

    st.markdown("""
        <div style="background-color:#1e1e1e; padding:15px; border-radius:10px; margin-bottom:20px;">
            <h3 style="color:#e63946;">Refinanced Loan Summary</h3>
            <p style="font-size:18px; color:white;">
                💰 <strong>New Payment:</strong> <span style="color:#f9c74f;">${:.2f}</span> {}<br>
                📊 <strong>Total Interest Paid (Refinanced):</strong> <span style="color:#f9c74f;">${:.2f}</span><br>
                🕒 <strong>Periods to Payoff (Refinanced):</strong> <span style="color:#f9c74f;">{} {}</span><br>
                📅 <strong>Refinanced Loan End Date:</strong> <span style="color:#f9c74f;">{}</span><br>
                💵 <strong>Total Refinanced Loan Cost:</strong> <span style="color:#f9c74f;">${:.2f}</span><br>
                💸 <strong>{}</strong>
            </p>
        </div>
    """.format(refinanced_payment, payment_frequency.lower(), refinanced_total_interest, refinanced_periods, payment_frequency.lower(), refinanced_loan_end_date.strftime('%B %d, %Y'), refinanced_total_loan_cost, savings_message), unsafe_allow_html=True)

    st.write("#### Comparison of Original Loan vs Refinanced Loan 📊")
    plt.figure(figsize=(10, 6))
    plt.plot(df["Period"], df["Remaining Balance"], label='Original Loan Balance', color='#e63946', linewidth=2)
    plt.plot(range(1, refinanced_periods + 1), refinanced_balances, label='Refinanced Loan Balance', color='blue', linewidth=2)
    plt.xlabel("Period")
    plt.ylabel("Loan Balance ($)")
    plt.title(f"Original vs Refinanced Loan Balance Over Time ({payment_frequency} Payments)")
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(plt)


st.markdown("---")


st.write("### Helpful Information about Student Loans 🎓")

st.markdown("""
#### Types of Student Loans
**Federal Loans**: These are loans offered by the federal government. They typically offer lower interest rates and more flexible repayment options.
- **Subsidized Loans**: The government pays the interest while you're in school.
- **Unsubsidized Loans**: Interest accrues while you're in school.

#### Loan Repayment Options
- **Income-Driven Repayment**: Payments are calculated based on your income and family size, and you may qualify for loan forgiveness after a certain number of years.
- **Standard Repayment**: Fixed monthly payments for 10 years. This is typically the fastest and most cost-effective option.
- **Refinancing**: You can refinance your student loans to lower the interest rate and/or change the repayment term, potentially saving on interest costs.
""")
