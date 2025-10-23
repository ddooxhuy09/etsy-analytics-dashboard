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

def get_customers_by_location(start_date: str = None, end_date: str = None, customer_type: str = 'all'):
    """Get customers by location"""
    sql = """SELECT dg.state_name as "State", 
                   COUNT(DISTINCT fs.customer_key) as "Customers", 
                   ROUND(COALESCE(SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)), 0), 2) as "Revenue (USD)" 
            FROM fact_sales fs 
            JOIN dim_geography dg ON fs.geography_key = dg.geography_key 
            JOIN dim_time dt ON fs.sale_date_key = dt.time_key
            WHERE dg.country_name = 'United States'"""
    
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
    
    sql += """ GROUP BY 1
               ORDER BY COUNT(DISTINCT fs.customer_key) DESC 
               LIMIT 12"""
    
    return execute_query(sql, tuple(params) if params else None)

def render_customers_by_location_description(start_date_str, end_date_str, customer_type):
    """Render description for customers by location chart"""
    if st.session_state.get('show_customers_by_location_description', False):
        with st.expander("📋 Customers by Location Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **KHÁCH HÀNG THEO TIỂU BANG (US) - USD**

            - **State**: Tên tiểu bang
            - **Customers**: Số khách hàng duy nhất
            - **Revenue (USD)**: Doanh thu ròng (USD)
            - **Lưu ý**: GROUP BY cột hiển thị để tăng tương thích
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_customers_by_location_description_btn", width='stretch'):
                    st.session_state.show_customers_by_location_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
