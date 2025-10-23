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

def get_customer_lifetime_value(start_date: str = None, end_date: str = None, customer_type: str = 'all', customer_lifespan_months: int = 12):
    """Get customer lifetime value"""
    sql = """SELECT ROUND(
                (
                    -- Average Revenue per Customer
                    (SELECT SUM(COALESCE(fs.item_total, 0)) 
                     FROM fact_sales fs 
                     JOIN dim_time dt ON fs.sale_date_key = dt.time_key
                     WHERE 1=1 AND dt.full_date >= %s AND dt.full_date <= %s) * 1.0 / 
                    NULLIF((SELECT COUNT(DISTINCT fs.customer_key) 
                            FROM fact_sales fs 
                            JOIN dim_time dt ON fs.sale_date_key = dt.time_key
                            WHERE 1=1 AND dt.full_date >= %s AND dt.full_date <= %s), 0)
                    *
                    -- Customer Lifespan
                    %s
                    -
                    -- Total Costs of Serving the Customer
                    (
                        SELECT 
                            SUM(COALESCE(fp.fees, 0)) +
                            SUM(COALESCE(fp.posted_fees, 0)) +
                            SUM(COALESCE(fp.adjusted_fees, 0)) +
                            SUM(COALESCE(dim_order.card_processing_fees, 0)) +
                            SUM(COALESCE(dim_order.adjusted_card_processing_fees, 0)) +
                            SUM(COALESCE(fs.discount_amount, 0)) +
                            SUM(COALESCE(fs.shipping_discount, 0))
                        FROM fact_sales fs
                        JOIN fact_payments fp ON fs.order_key = fp.order_key
                        JOIN dim_order ON fs.order_key = dim_order.order_key
                        JOIN dim_time dt ON fs.sale_date_key = dt.time_key
                        WHERE 1=1 AND dt.full_date >= %s AND dt.full_date <= %s
                    ) * 1.0 / 
                    NULLIF((SELECT COUNT(DISTINCT fs.customer_key) 
                            FROM fact_sales fs 
                            JOIN dim_time dt ON fs.sale_date_key = dt.time_key
                            WHERE 1=1 AND dt.full_date >= %s AND dt.full_date <= %s), 0)
                )
            , 2) AS "CLV (USD)" """
    
    params = []
    if start_date and end_date:
        params = [start_date, end_date, start_date, end_date, customer_lifespan_months, start_date, end_date, start_date, end_date]
    else:
        # Use default date range if not provided
        params = ['2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31', customer_lifespan_months, '2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31']
    
    return execute_query(sql, tuple(params))

def render_customer_lifetime_value_description(start_date_str, end_date_str, customer_type):
    """Render description for customer lifetime value chart"""
    if st.session_state.get('show_customer_lifetime_value_description', False):
        with st.expander("📋 Customer Lifetime Value Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **GIÁ TRỊ KHÁCH HÀNG TRỌN ĐỜI (CLV) - USD**

            **Công thức:** CLV = (Average Revenue per Customer × Customer Lifespan) − Total Costs of Serving the Customer

            - **Average Revenue per Customer**: Doanh thu trung bình mỗi khách hàng
            - **Customer Lifespan**: Tuổi thọ khách hàng (có thể điều chỉnh qua filter customer_lifespan_months, mặc định 12 tháng)
            - **Total Costs of Serving**: Tổng chi phí phục vụ khách hàng bao gồm:
              - fees, posted_fees, adjusted_fees (từ fact_payments) (Fees, Posted Fees, Adjusted Fees trong file EtsyDirectCheckoutPayments2025-1.csv)
              - card_processing_fees, adjusted_card_processing_fees (từ dim_order) (Card Processing Fees, Adjusted Card Processing Fees trong file EtsySoldOrders2025-1.csv)
              - discount_amount, shipping_discount (từ fact_sales) (Discount Amount, Shipping Discount trong file EtsySoldOrderItems2025-1.csv)

            Chỉ số này cho thấy lợi nhuận thực tế từ mỗi khách hàng trong suốt vòng đời (USD).
            Có thể điều chỉnh Customer Lifespan theo nhu cầu phân tích (theo ngày, tháng, năm).
            """))

            st.markdown(textwrap.dedent(f"""
            **Filters Applied:**

            - From Date: {start_date_str or 'All time'}
            - To Date: {end_date_str or 'Present'}
            - Customer Type: {get_customer_type_display(customer_type)}
            """))
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_customer_lifetime_value_description_btn", width='stretch'):
                    st.session_state.show_customer_lifetime_value_description = False
                    st.rerun()

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')
