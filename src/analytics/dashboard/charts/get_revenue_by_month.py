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

def get_revenue_by_month(start_date: str = None, end_date: str = None, customer_type: str = 'all'):
    """Get revenue by month"""
    sql = """
    SELECT 
        dt.year || '-' || LPAD(dt.month::text, 2, '0') as "Month",
        ROUND(COALESCE(SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)), 0), 2) as "Revenue (USD)"
    FROM fact_sales fs
    JOIN dim_time dt ON fs.sale_date_key = dt.time_key
    WHERE 1=1
    """   
    params = []
    
    if start_date:
        sql += " AND dt.full_date >= %s"
        params.append(start_date)
    
    if end_date:
        sql += " AND dt.full_date <= %s"
        params.append(end_date)
    
    if customer_type == 'new':
        sql += """ AND fs.customer_key IN (
            SELECT customer_key 
            FROM fact_sales 
            GROUP BY customer_key 
            HAVING COUNT(DISTINCT order_key) = 1
        )"""
    elif customer_type == 'return':
        sql += """ AND fs.customer_key IN (
            SELECT customer_key 
            FROM fact_sales 
            GROUP BY customer_key 
            HAVING COUNT(DISTINCT order_key) > 1
        )"""
    
    sql += """
    GROUP BY dt.year, dt.month
    ORDER BY dt.year, dt.month
    """
    
    return execute_query(sql, tuple(params) if params else None)

def render_revenue_by_month_description(start_date_str, end_date_str, customer_type):
    """Render description for revenue by month chart"""
    if st.session_state.get('show_revenue_by_month_description', False):
        with st.expander("📋 Revenue by Month Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **DOANH THU THEO THÁNG (BIỂU ĐỒ CỘT) - USD**

            **SQL Query:**
            ```sql
            SELECT 
                dt.year || '-' || LPAD(dt.month::text, 2, '0') as "Month",
                ROUND(COALESCE(SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)), 0), 2) as "Revenue (USD)"
            FROM fact_sales fs
            JOIN dim_time dt ON fs.sale_date_key = dt.time_key
            WHERE 1=1
            [[ AND dt.full_date >= start_date ]]
            [[ AND dt.full_date <= end_date ]]
            [[ AND customer_type filter ]]
            GROUP BY dt.year, dt.month
            ORDER BY dt.year, dt.month
            ```

            **Giải thích:**
            - **Month**: Tháng (định dạng YYYY-MM)
            - **Revenue (USD)**: Doanh thu ròng theo tháng (USD)
            - **item_total**: Tổng giá trị sản phẩm bán (từ bảng fact_sales - Item Total trong file EtsySoldOrderItems2025-1.csv)
            - **discount_amount**: Số tiền giảm giá (từ bảng fact_sales - Discount Amount trong file EtsySoldOrderItems2025-1.csv)

            **Kết quả**: Biểu đồ cột hiển thị doanh thu từng tháng (USD)
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_revenue_by_month_description_btn", width='stretch'):
                    st.session_state.show_revenue_by_month_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
