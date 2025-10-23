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

def get_new_vs_returning_customer_sales(start_date: str = None, end_date: str = None, customer_type: str = 'all'):
    """Get new vs returning customer sales"""
    sql = """SELECT CASE WHEN customer_orders.order_count = 1 THEN 'New Customers' ELSE 'Returning Customers' END as "Customer Type",
                  ROUND(SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)), 2) as "Revenue (USD)" 
           FROM fact_sales fs 
           JOIN dim_time dtime ON fs.sale_date_key = dtime.time_key
           JOIN (
               SELECT customer_key, COUNT(DISTINCT order_key) as order_count 
               FROM fact_sales 
               GROUP BY customer_key
           ) customer_orders ON fs.customer_key = customer_orders.customer_key
           WHERE 1=1"""
    
    params = []
    if start_date:
        sql += " AND dtime.full_date >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND dtime.full_date <= %s"
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
               ORDER BY SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)) DESC"""
    
    return execute_query(sql, tuple(params) if params else None)

def render_new_vs_returning_customer_sales_description(start_date_str, end_date_str, customer_type):
    """Render description for new vs returning customer sales chart"""
    if st.session_state.get('show_new_vs_returning_customer_sales_description', False):
        with st.expander("📋 New vs Returning Customer Sales Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **DOANH THU: KHÁCH HÀNG MỚI vs. KHÁCH HÀNG QUAY LẠI (USD)**

            **Phân nhóm theo kiểu khách hàng:**
            - **New Customers**: Khách có đúng 1 đơn hàng (order_count = 1)
            - **Returning Customers**: Khách có > 1 đơn hàng

            **Chỉ số hiển thị:**
            - **Revenue (USD)** = SUM(item_total) - SUM(discount_amount)
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_new_vs_returning_customer_sales_description_btn", width='stretch'):
                    st.session_state.show_new_vs_returning_customer_sales_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
