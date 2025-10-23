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

def get_total_customers(start_date: str = None, end_date: str = None, customer_type: str = 'all'):
    """Get total customers"""
    sql = """SELECT COUNT(DISTINCT fs.customer_key) as "Total Customers" 
            FROM fact_sales fs 
            JOIN dim_time dt ON fs.sale_date_key = dt.time_key
            WHERE 1=1"""
    
    params = []
    if start_date:
        sql += " AND dt.full_date >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND dt.full_date <= %s"
        params.append(end_date)
    
    if customer_type == 'new':
        sql += """ AND fs.customer_key IN (
            SELECT customer_key FROM fact_sales GROUP BY customer_key HAVING COUNT(DISTINCT order_key) = 1
        )"""
    elif customer_type == 'return':
        sql += """ AND fs.customer_key IN (
            SELECT customer_key FROM fact_sales GROUP BY customer_key HAVING COUNT(DISTINCT order_key) > 1
        )"""
    
    return execute_query(sql, tuple(params) if params else None)

def render_get_total_customers_description(start_date_str, end_date_str, customer_type):
    """Render description for total customers KPI"""
    if st.session_state.get('show_total_customers_description', False):
        with st.expander("📋 Total Customers Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **TỔNG SỐ KHÁCH HÀNG**

            **Công thức:** Total Customers = COUNT(DISTINCT customer_key)

            - **customer_key**: Khóa duy nhất của khách hàng (từ bảng fact_sales)
            - **COUNT(DISTINCT)**: Đếm số khách hàng không trùng lặp
            - **Kết quả**: Tổng số khách hàng đã mua hàng
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            # Close button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_total_customers_description_btn", width='stretch'):
                    st.session_state.show_total_customers_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
