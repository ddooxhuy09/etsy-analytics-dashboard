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

def get_customer_acquisition_cost(start_date: str = None, end_date: str = None):
    """Get customer acquisition cost"""
    sql = """SELECT ROUND(
                COALESCE((
                    SELECT SUM(COALESCE(fft.fees_and_taxes, 0))
                    FROM fact_financial_transactions fft
                    JOIN dim_time dt1 ON fft.transaction_date_key = dt1.time_key
                    WHERE fft.transaction_type = 'Marketing'
                    AND dt1.full_date >= %s AND dt1.full_date <= %s
                ), 0)
                /
                NULLIF((
                    SELECT COUNT(DISTINCT fs.customer_key)
                    FROM fact_sales fs
                    JOIN dim_time dt2 ON fs.sale_date_key = dt2.time_key
                    WHERE fs.customer_key IN (
                        SELECT customer_key
                        FROM fact_sales
                        GROUP BY customer_key
                        HAVING COUNT(DISTINCT order_key) = 1
                    )
                    AND dt2.full_date >= %s AND dt2.full_date <= %s
                ), 0)
            , 2) AS "CAC (USD)" """
    
    params = []
    if start_date and end_date:
        params = [start_date, end_date, start_date, end_date]
    else:
        # Use default date range if not provided
        params = ['2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31']
    
    return execute_query(sql, tuple(params))

def render_customer_acquisition_cost_description(start_date_str, end_date_str, customer_type):
    """Render description for customer acquisition cost chart"""
    if st.session_state.get('show_customer_acquisition_cost_description', False):
        with st.expander("📋 Customer Acquisition Cost Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **CHI PHÍ THU HÚT KHÁCH HÀNG (CAC) - USD**

            **Công thức:** CAC = Marketing Spend / New Customers

            - **Marketing Spend**: Tổng chi phí marketing (SUM(fees_and_taxes) từ fact_financial_transactions WHERE transaction_type = 'Marketing' - Fees and Taxes trong file etsy_statement_2025_1.csv)
            - **New Customers**: Số khách hàng mới (COUNT(DISTINCT customer_key) WHERE COUNT(order_key) = 1)
            - **Kết quả**: Chi phí trung bình để thu hút 1 khách hàng mới (USD)

            Chỉ số này giúp đánh giá hiệu quả của các chiến dịch marketing.
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_customer_acquisition_cost_description_btn", width='stretch'):
                    st.session_state.show_customer_acquisition_cost_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
