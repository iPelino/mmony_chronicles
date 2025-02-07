import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Connect to the SQLite database
conn = sqlite3.connect("db/transactions_by_type_v3.db")

# =====================================
# SQL Query Functions for Reports
# =====================================

def get_daily_transactions():
    """Get daily transaction volume by type."""
    query = """
        WITH all_txns AS (
            SELECT 'incoming' AS type, date_time, amount FROM incoming_money
            UNION ALL
            SELECT 'payment_to_code' AS type, date_time, amount FROM payment_to_code_holder
            UNION ALL
            SELECT 'mobile_transfer' AS type, date_time, amount FROM transfer_to_mobile
            UNION ALL
            SELECT 'bank_deposit' AS type, date_time, amount FROM bank_deposits
            UNION ALL
            SELECT 'airtime_bill' AS type, date_time, amount FROM airtime_bill_payments
            UNION ALL
            SELECT 'cash_power_bill' AS type, date_time, amount FROM cash_power_bill_payments
            UNION ALL
            SELECT 'third_party' AS type, date_time, amount FROM third_party_transactions
            UNION ALL
            SELECT 'withdrawal' AS type, date_time, amount FROM withdrawals_from_agents
            UNION ALL
            SELECT 'bank_transfer' AS type, date_time, amount FROM bank_transfers
        )
        SELECT 
            DATE(date_time) AS day,
            type,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_amount
        FROM all_txns
        GROUP BY day, type
    """
    return pd.read_sql(query, conn)

def get_fee_analysis():
    """Get total fees by transaction type."""
    query = """
        SELECT 'mobile_transfer' AS type, SUM(fee) AS total_fee FROM transfer_to_mobile
        UNION ALL
        SELECT 'airtime_bill' AS type, SUM(fee) AS total_fee FROM airtime_bill_payments
        UNION ALL
        SELECT 'cash_power_bill' AS type, SUM(fee) AS total_fee FROM cash_power_bill_payments
    """
    return pd.read_sql(query, conn)

def get_top_agents():
    """Identify top agents by withdrawal volume."""
    query = """
        SELECT 
            agent_name,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_amount
        FROM withdrawals_from_agents
        GROUP BY agent_name
        ORDER BY total_amount DESC
        LIMIT 10
    """
    return pd.read_sql(query, conn)

def get_bundle_analysis():
    """Analyze internet/voice bundle purchases."""
    internet_query = """
        SELECT bundle_size, COUNT(*) AS purchase_count 
        FROM internet_bundle_purchases 
        GROUP BY bundle_size
    """
    voice_query = """
        SELECT minutes, COUNT(*) AS purchase_count 
        FROM voice_bundle_purchases 
        GROUP BY minutes
    """
    return {
        "internet": pd.read_sql(internet_query, conn),
        "voice": pd.read_sql(voice_query, conn)
    }
def get_top_recipients():
    """Identify top recipients of mobile transfers."""
    query = """
        SELECT 
            recipient,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_amount
        FROM transfer_to_mobile
        GROUP BY recipient
        ORDER BY total_amount DESC
        LIMIT 30
    """
    return pd.read_sql(query, conn)

def get_top_recipients_code_holders():
    """Identify top recipients of code holder payments."""
    query = """
        SELECT 
            recipient,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_amount
        FROM payment_to_code_holder
        GROUP BY recipient
        ORDER BY total_amount DESC
        LIMIT 30
    """
    return pd.read_sql(query, conn)

# =====================================
# Streamlit Dashboard
# =====================================

st.set_page_config(layout="wide")
st.title("Mobile Money Transaction Dashboard")

# ------------------
# Report 1: Daily Transactions
# ------------------
st.subheader("Daily Transaction Volume")
daily_txns = get_daily_transactions()
fig = px.line(
    daily_txns,
    x="day",
    y="transaction_count",
    color="type",
    title="Transactions Over Time"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------
# Report 1.5: Daily Transaction Amount
# ------------------
st.subheader("Daily Transaction Amount")
fig = px.line(
    daily_txns,
    x="day",
    y="total_amount",
    color="type",
    title="Transaction Amount Over Time"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------
# Custom Report - Top Mobile Trasfer Recipients
# ------------------
st.subheader("Top Mobile Transfer Recipients")
top_recipients = get_top_recipients()
fig = px.bar(
    top_recipients,
    x="recipient",
    y="total_amount",
    title="Top Mobile Transfer Recipients"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------
# Custom Report - Top Code Holder Recipients
# ------------------
st.subheader("Top Code Holder Recipients")
top_recipients_code_holders = get_top_recipients_code_holders()
fig = px.bar(
    top_recipients_code_holders,
    x="recipient",
    y="total_amount",
    title="Top Code Holder Recipients"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------
# Report 2: Fee Analysis
# ------------------
# st.subheader("Fee Breakdown by Transaction Type")
# fee_data = get_fee_analysis()
# fig = px.bar(
#     fee_data,
#     x="type",
#     y="total_fee",
#     title="Total Fees Paid"
# )
# st.plotly_chart(fig, use_container_width=True)

# ------------------
# Report 3: Top Agents
# ------------------
st.subheader("Top Agents by Withdrawal Volume")
top_agents = get_top_agents()
fig = px.bar(
    top_agents,
    x="agent_name",
    y="total_amount",
    title="Agent Performance"
)
st.plotly_chart(fig, use_container_width=True)

# ------------------
# Report 4: Bundle Analysis
# ------------------
st.subheader("Bundle Purchases")
bundle_data = get_bundle_analysis()

col1, col2 = st.columns(2)
with col1:
    fig = px.pie(
        bundle_data["internet"],
        names="bundle_size",
        values="purchase_count",
        title="Internet Bundle Sizes"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.pie(
        bundle_data["voice"],
        names="minutes",
        values="purchase_count",
        title="Voice Bundle Minutes"
    )
    st.plotly_chart(fig, use_container_width=True)

# Close connection
conn.close()