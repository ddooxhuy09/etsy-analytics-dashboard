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

def get_total_sales_by_product(start_date: str = None, end_date: str = None, customer_type: str = 'all'):
    """Get total sales by product"""
    sql = """SELECT CASE WHEN LENGTH(dp.title) > 30 THEN LEFT(dp.title, 27) || '...' ELSE dp.title END as "Product", 
                   ROUND(COALESCE(SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)), 0), 2) as "Revenue (USD)" 
            FROM fact_sales fs 
            JOIN dim_product dp ON fs.product_key = dp.product_key 
            JOIN dim_time dt ON fs.sale_date_key = dt.time_key
            WHERE dp.is_current = true"""
    
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
               ORDER BY SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)) DESC 
               LIMIT 10"""
    
    return execute_query(sql, tuple(params) if params else None)

def render_total_sales_by_product_description(start_date_str, end_date_str, customer_type):
    """Render description for total sales by product chart"""
    if st.session_state.get('show_total_sales_by_product_description', False):
        with st.expander("📋 Total Sales by Product Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **DOANH THU THEO SẢN PHẨM (TOP 10) - USD**

            **Công thức:** Revenue = SUM(item_total) - SUM(discount_amount) theo từng sản phẩm

            - **Product**: Tên sản phẩm (rút gọn tối đa 30 ký tự để dễ đọc)
            - **Revenue (USD)**: Doanh thu ròng của sản phẩm (USD)
            - **Lấy TOP 10 sản phẩm có doanh thu cao nhất**
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_total_sales_by_product_description_btn", width='stretch'):
                    st.session_state.show_total_sales_by_product_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
