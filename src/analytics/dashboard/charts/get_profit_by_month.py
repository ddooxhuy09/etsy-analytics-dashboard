import streamlit as st
import pandas as pd
import sys
import os
import textwrap

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from src.analytics.utils.postgres_connection import execute_query_with_cache

def execute_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """Execute SQL query and return DataFrame"""
    return execute_query_with_cache(sql, params, ttl=300)

def get_profit_by_month(start_date: str = None, end_date: str = None, customer_type: str = 'all'):
    """Get profit by month based on fact_payments.net_amount"""
    sql = """
    SELECT 
        dt.year || '-' || LPAD(dt.month::text, 2, '0') as "Month",
        ROUND(COALESCE(SUM(COALESCE(fp.net_amount, 0)), 0), 2) as "Profit (USD)"
    FROM fact_payments fp
    JOIN dim_time dt ON fp.payment_date_key = dt.time_key
    WHERE 1=1
    """

    params = []

    if start_date:
        sql += " AND dt.full_date >= %s"
        params.append(start_date)

    if end_date:
        sql += " AND dt.full_date <= %s"
        params.append(end_date)

    sql += """
    GROUP BY dt.year, dt.month
    ORDER BY dt.year, dt.month
    """

    return execute_query(sql, tuple(params) if params else None)

def render_profit_by_month_description(start_date_str, end_date_str, customer_type):
    """Render description for profit by month chart"""
    if st.session_state.get('show_profit_by_month_description', False):
        with st.expander("📋 Profit by Month Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **LỢI NHUẬN THEO THÁNG (USD)**

            - **Công thức:** Profit (USD) = SUM(fact_payments.net_amount là cột Net Amount trong file EtsyDirectCheckoutPayments2025-1.csv)
            - Sử dụng ngày theo `payment_date_key` trong bảng `fact_payments`
            - Nhóm theo tháng để tổng hợp lợi nhuận theo từng tháng
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))

            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_profit_by_month_description_btn", width='stretch'):
                    st.session_state.show_profit_by_month_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')


