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

def get_customer_retention_rate(start_date: str = None, end_date: str = None, customer_type: str = 'all'):
    """Get customer retention rate"""
    sql = """SELECT ROUND(
                COUNT(DISTINCT CASE WHEN order_count > 1 THEN fs.customer_key END) * 100.0 / NULLIF(COUNT(DISTINCT fs.customer_key), 0),
            2) AS "Retention Rate (%)"
            FROM fact_sales fs
            JOIN (SELECT customer_key, COUNT(DISTINCT order_key) AS order_count FROM fact_sales GROUP BY 1) co ON fs.customer_key = co.customer_key
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

def render_customer_retention_rate_description(start_date_str, end_date_str, customer_type):
    """Render description for customer retention rate chart"""
    if st.session_state.get('show_retention_rate_description', False):
        with st.expander("📋 Customer Retention Rate Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **TỶ LỆ GIỮ CHÂN KHÁCH HÀNG**

            - **Công thức**: Retention Rate = (Khách hàng quay lại / Tổng khách hàng) × 100
            - **Khách hàng quay lại**: Customer có > 1 đơn hàng (order_count > 1)
            - **Tổng khách hàng**: Tất cả khách hàng trong kỳ (có thể lọc theo loại khách hàng)
            - **Theo dõi khả năng giữ chân khách hàng**
            - **Chỉ số quan trọng cho CLV và chiến lược marketing**
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_customer_retention_rate_description_btn", width='stretch'):
                    st.session_state.show_retention_rate_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
