import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import textwrap

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.analytics.utils.postgres_connection import execute_query

def get_revenue_comparison_by_month(month1_year, month1_month, month2_year, month2_month):
    """
    Get revenue comparison between two specific months
    
    Args:
        month1_year: Year for first month (e.g., 2025)
        month1_month: Month number for first month (1-12)
        month2_year: Year for second month (e.g., 2024)
        month2_month: Month number for second month (1-12)
    
    Returns:
        DataFrame with revenue data for both months
    """
    
    # Calculate start and end dates for both months
    month1_start = datetime(month1_year, month1_month, 1).date()
    if month1_month == 12:
        month1_end = datetime(month1_year + 1, 1, 1).date() - pd.Timedelta(days=1)
    else:
        month1_end = datetime(month1_year, month1_month + 1, 1).date() - pd.Timedelta(days=1)
    
    month2_start = datetime(month2_year, month2_month, 1).date()
    if month2_month == 12:
        month2_end = datetime(month2_year + 1, 1, 1).date() - pd.Timedelta(days=1)
    else:
        month2_end = datetime(month2_year, month2_month + 1, 1).date() - pd.Timedelta(days=1)
    
    # SQL query for daily revenue comparison between two months
    sql = """
    WITH month1_daily AS (
        SELECT 
            dt.full_date as date,
            ROUND(COALESCE(SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)), 0), 2) as revenue,
            'Month 1' as month_label,
            dt.day_of_month as day_of_month
        FROM fact_sales fs 
        JOIN dim_time dt ON fs.sale_date_key = dt.time_key
        WHERE dt.full_date >= %s AND dt.full_date <= %s
        GROUP BY dt.full_date, dt.day_of_month
    ),
    month2_daily AS (
        SELECT 
            dt.full_date as date,
            ROUND(COALESCE(SUM(COALESCE(fs.item_total, 0) - COALESCE(fs.discount_amount, 0)), 0), 2) as revenue,
            'Month 2' as month_label,
            dt.day_of_month as day_of_month
        FROM fact_sales fs 
        JOIN dim_time dt ON fs.sale_date_key = dt.time_key
        WHERE dt.full_date >= %s AND dt.full_date <= %s
        GROUP BY dt.full_date, dt.day_of_month
    )
    SELECT 
        date as "Date",
        revenue as "Revenue (USD)",
        month_label as "Month",
        day_of_month as "Day"
    FROM month1_daily
    UNION ALL
    SELECT 
        date as "Date",
        revenue as "Revenue (USD)",
        month_label as "Month",
        day_of_month as "Day"
    FROM month2_daily
    ORDER BY "Month", "Day"
    """
    
    params = [
        month1_start, month1_end,  # month1_daily
        month2_start, month2_end   # month2_daily
    ]
    
    return execute_query(sql, tuple(params))

def get_month_aggregates(month_start, month_end):
    """Return aggregates for a month: orders_count, revenue, profit."""
    # Orders count from fact_sales (distinct orders)
    orders_sql = """
    SELECT COUNT(DISTINCT fs.order_key) AS orders_count
    FROM fact_sales fs
    JOIN dim_time dt ON fs.sale_date_key = dt.time_key
    WHERE dt.full_date >= %s AND dt.full_date <= %s
    """
    orders_df = execute_query(orders_sql, (month_start, month_end))
    orders_count = int(orders_df.iloc[0, 0]) if not orders_df.empty else 0

    # Revenue and Profit from fact_payments
    rev_profit_sql = """
    SELECT 
        COALESCE(SUM(COALESCE(fp.gross_amount, 0)), 0) AS revenue,
        COALESCE(SUM(COALESCE(fp.net_amount, 0)), 0)   AS profit
    FROM fact_payments fp
    JOIN dim_time dt ON fp.payment_date_key = dt.time_key
    WHERE dt.full_date >= %s AND dt.full_date <= %s
    """
    rp_df = execute_query(rev_profit_sql, (month_start, month_end))
    revenue = float(rp_df.iloc[0, 0]) if not rp_df.empty else 0.0
    profit = float(rp_df.iloc[0, 1]) if not rp_df.empty else 0.0

    return {
        "orders_count": orders_count,
        "revenue": revenue,
        "profit": profit,
    }

def get_comparison_percentages(month1_year, month1_month, month2_year, month2_month):
    """Compute Order Total %, Revenue %, Profit % for month1 vs month2."""
    # Calculate date ranges
    m1_start = datetime(month1_year, month1_month, 1).date()
    if month1_month == 12:
        m1_end = (datetime(month1_year + 1, 1, 1) - pd.Timedelta(days=1)).date()
    else:
        m1_end = (datetime(month1_year, month1_month + 1, 1) - pd.Timedelta(days=1)).date()

    m2_start = datetime(month2_year, month2_month, 1).date()
    if month2_month == 12:
        m2_end = (datetime(month2_year + 1, 1, 1) - pd.Timedelta(days=1)).date()
    else:
        m2_end = (datetime(month2_year, month2_month + 1, 1) - pd.Timedelta(days=1)).date()

    m1 = get_month_aggregates(m1_start, m1_end)
    m2 = get_month_aggregates(m2_start, m2_end)

    def ratio_pct(a, b):
        if b and b != 0:
            return (a / b) * 100.0
        return None

    return {
        "orders_pct": ratio_pct(m1["orders_count"], m2["orders_count"]),
        "revenue_pct": ratio_pct(m1["revenue"], m2["revenue"]),
        "profit_pct": ratio_pct(m1["profit"], m2["profit"]),
        "m1": m1,
        "m2": m2,
    }

def render_revenue_comparison_by_month_description(month1_year, month1_month, month2_year, month2_month):
    """Render description for revenue comparison chart"""
    if st.session_state.get('show_revenue_comparison_by_month_description', False):
        with st.expander("📋 Revenue Comparison by Month Description", expanded=False):
            st.markdown(textwrap.dedent("""
            **SO SÁNH DOANH THU THEO NGÀY TRONG THÁNG**

            **Công thức:** Daily Revenue = SUM(item_total - discount_amount) GROUP BY date

            - **item_total**: Tổng giá trị sản phẩm bán (từ bảng fact_sales - Item Total trong file EtsySoldOrderItems2025-1.csv)
            - **discount_amount**: Số tiền giảm giá (từ bảng fact_sales - Discount Amount trong file EtsySoldOrderItems2025-1.csv)
            - **So sánh theo ngày**: Hiển thị doanh thu từng ngày trong 2 tháng được chọn
            - **Kết quả**: Biểu đồ line với 2 đường so sánh doanh thu theo ngày
            - **X-axis**: Ngày trong tháng (1-31)
            - **Y-axis**: Doanh thu (USD)

            Chart này giúp so sánh xu hướng bán hàng hàng ngày giữa 2 tháng khác nhau.
            """))

            # Show formulas for comparison metrics
            st.markdown("""
                **Công thức các chỉ số so sánh:**
                
                - **Order Total %** = (Số đơn hàng tháng 1 / Số đơn hàng tháng 2) × 100
                - **Revenue %** = (Tổng doanh thu tháng 1 / Tổng doanh thu tháng 2) × 100
                - **Profit %** = (Tổng lợi nhuận tháng 1 / Tổng lợi nhuận tháng 2) × 100
            """)
            
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            month1_name = month_names[month1_month - 1]
            month2_name = month_names[month2_month - 1]
            
            st.markdown(textwrap.dedent(f"""
            **Comparison Period:**

            - Month 1: {month1_name} {month1_year}
            - Month 2: {month2_name} {month2_year}
            """))

            # Display computed percentages for the selected months
            try:
                cmp = get_comparison_percentages(month1_year, month1_month, month2_year, month2_month)
                order_pct = cmp.get("orders_pct")
                revenue_pct = cmp.get("revenue_pct")
                profit_pct = cmp.get("profit_pct")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        label="Order Total %",
                        value=f"{order_pct:.1f}%" if order_pct is not None else "N/A",
                        help="(Orders M1 / Orders M2) * 100"
                    )
                with col2:
                    st.metric(
                        label="Revenue %",
                        value=f"{revenue_pct:.1f}%" if revenue_pct is not None else "N/A",
                        help="(Revenue M1 / Revenue M2) * 100"
                    )
                with col3:
                    st.metric(
                        label="Profit %",
                        value=f"{profit_pct:.1f}%" if profit_pct is not None else "N/A",
                        help="(Profit M1 / Profit M2) * 100"
                    )
            except Exception:
                pass
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_revenue_comparison_by_month_description_btn", width='stretch'):
                    st.session_state.show_revenue_comparison_by_month_description = False
                    st.rerun()

def get_month_name(month_number):
    """Get month name from month number"""
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    return month_names[month_number - 1]
