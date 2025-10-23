"""
Etsy Analytics Dashboard - Streamlit Cloud Version
Main entry point for Streamlit Community Cloud deployment
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import database connection function
from src.analytics.utils.postgres_connection import execute_query_with_cache

# Import chart functions
from src.analytics.dashboard.charts.get_total_revenue import get_total_revenue, render_get_total_revenue_description
from src.analytics.dashboard.charts.get_total_orders import get_total_orders, render_get_total_orders_description
from src.analytics.dashboard.charts.get_total_customers import get_total_customers, render_get_total_customers_description
from src.analytics.dashboard.charts.get_average_order_value import get_average_order_value, render_get_average_order_value_description
from src.analytics.dashboard.charts.get_revenue_by_month import get_revenue_by_month, render_revenue_by_month_description
from src.analytics.dashboard.charts.get_profit_by_month import get_profit_by_month, render_profit_by_month_description
from src.analytics.dashboard.charts.get_new_vs_returning_customer_sales import get_new_vs_returning_customer_sales, render_new_vs_returning_customer_sales_description
from src.analytics.dashboard.charts.get_new_customers_over_time import get_new_customers_over_time, render_new_customers_over_time_description
from src.analytics.dashboard.charts.get_customers_by_location import get_customers_by_location, render_customers_by_location_description
from src.analytics.dashboard.charts.get_total_sales_by_product import get_total_sales_by_product, render_total_sales_by_product_description
from src.analytics.dashboard.charts.get_customer_acquisition_cost import get_customer_acquisition_cost, render_customer_acquisition_cost_description
from src.analytics.dashboard.charts.get_customer_lifetime_value import get_customer_lifetime_value, render_customer_lifetime_value_description
from src.analytics.dashboard.charts.get_customer_retention_rate import get_customer_retention_rate, render_customer_retention_rate_description
from src.analytics.dashboard.charts.get_total_orders_by_month import get_total_orders_by_month, render_total_orders_by_month_description
from src.analytics.dashboard.charts.get_average_order_value_over_time import get_average_order_value_over_time, render_average_order_value_over_time_description
from src.analytics.dashboard.charts.get_revenue_comparison_by_month import get_revenue_comparison_by_month, render_revenue_comparison_by_month_description, get_month_name
from src.analytics.dashboard.charts.get_cac_clv_ratio_over_time import get_cac_clv_ratio_over_time, render_cac_clv_ratio_over_time_description
from src.analytics.dashboard.profit_loss_statement.profit_loss_statement import render_profit_loss_statement
from src.analytics.reports.streamlit_account_statement import render_account_statement


def toggle_description(description_key):
    """Toggle description state using callback"""
    st.session_state[description_key] = not st.session_state.get(description_key, False)

def create_description_button(button_key, description_key, text="📋 Show Description", width='stretch'):
    """Create a description button with proper callback"""
    if st.button(text, key=button_key, width=width):
        st.session_state[description_key] = not st.session_state.get(description_key, False)
        st.rerun()
    return False

def get_customer_type_display(customer_type):
    """Get customer type display name"""
    mapping = {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}
    return mapping.get(customer_type, 'All Customers')


def render_dashboard():
    """Render dashboard tab content"""
    
    # Sidebar filters
    st.sidebar.header("📊 Dashboard Filters")
    
    # Month/Year selection
    st.sidebar.subheader("📅 Quick Date Selection")
    
    # Year selection
    current_year = datetime.now().year
    year_options = ["Select Year"] + list(range(2020, current_year + 2))
    selected_year = st.sidebar.selectbox(
        "Select Year",
        options=year_options,
        index=0,  # Default to "Select Year"
        key="selected_year"
    )
    
    # Month selection
    month_names = [
        "Select Month", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    selected_month = st.sidebar.selectbox(
        "Select Month",
        options=month_names,
        index=0,  # Default to "Select Month"
        key="selected_month"
    )
    
    # Calculate start and end dates for the selected month/year
    if selected_year != "Select Year":
        if selected_month != "Select Month":
            # Specific month selected
            month_num = month_names.index(selected_month)
            start_date = datetime(selected_year, month_num, 1)
            if month_num == 12:
                end_date = datetime(selected_year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(selected_year, month_num + 1, 1) - timedelta(days=1)
        else:
            # Entire year selected
            start_date = datetime(selected_year, 1, 1)
            end_date = datetime(selected_year, 12, 31)
    else:
        # No specific date selected - show all data
        start_date = None
        end_date = None
    
    # Customer type filter
    st.sidebar.subheader("👥 Customer Filter")
    customer_type = st.sidebar.selectbox(
        "Customer Type",
        options=["all", "new", "return"],
        format_func=lambda x: get_customer_type_display(x),
        key="customer_type_filter"
    )
    
    # Main dashboard content
    st.title("📊 Etsy Analytics Dashboard")
    st.markdown("---")
    
    # Key Metrics Row
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = get_total_revenue(start_date, end_date, customer_type)
        st.metric(
            label="💰 Total Revenue",
            value=f"${total_revenue:,.2f}",
            help="Total revenue from all sales"
        )
        create_description_button("revenue_desc_btn", "revenue_description")
        if st.session_state.get("revenue_description", False):
            render_get_total_revenue_description()
    
    with col2:
        total_orders = get_total_orders(start_date, end_date, customer_type)
        st.metric(
            label="📦 Total Orders",
            value=f"{total_orders:,}",
            help="Total number of orders"
        )
        create_description_button("orders_desc_btn", "orders_description")
        if st.session_state.get("orders_description", False):
            render_get_total_orders_description()
    
    with col3:
        total_customers = get_total_customers(start_date, end_date, customer_type)
        st.metric(
            label="👥 Total Customers",
            value=f"{total_customers:,}",
            help="Total number of unique customers"
        )
        create_description_button("customers_desc_btn", "customers_description")
        if st.session_state.get("customers_description", False):
            render_get_total_customers_description()
    
    with col4:
        avg_order_value = get_average_order_value(start_date, end_date, customer_type)
        st.metric(
            label="💵 Average Order Value",
            value=f"${avg_order_value:.2f}",
            help="Average value per order"
        )
        create_description_button("aov_desc_btn", "aov_description")
        if st.session_state.get("aov_description", False):
            render_get_average_order_value_description()
    
    st.markdown("---")
    
    # Charts Section
    st.subheader("📊 Revenue & Profit Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            get_revenue_by_month(start_date, end_date, customer_type),
            use_container_width=True
        )
        create_description_button("revenue_month_desc_btn", "revenue_month_description")
        if st.session_state.get("revenue_month_description", False):
            render_revenue_by_month_description()
    
    with col2:
        st.plotly_chart(
            get_profit_by_month(start_date, end_date, customer_type),
            use_container_width=True
        )
        create_description_button("profit_month_desc_btn", "profit_month_description")
        if st.session_state.get("profit_month_description", False):
            render_profit_by_month_description()
    
    st.markdown("---")
    
    # Customer Analysis
    st.subheader("👥 Customer Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            get_new_vs_returning_customer_sales(start_date, end_date),
            use_container_width=True
        )
        create_description_button("new_returning_desc_btn", "new_returning_description")
        if st.session_state.get("new_returning_description", False):
            render_new_vs_returning_customer_sales_description()
    
    with col2:
        st.plotly_chart(
            get_new_customers_over_time(start_date, end_date),
            use_container_width=True
        )
        create_description_button("new_customers_desc_btn", "new_customers_description")
        if st.session_state.get("new_customers_description", False):
            render_new_customers_over_time_description()
    
    # Geographic Analysis
    st.subheader("🌍 Geographic Analysis")
    st.plotly_chart(
        get_customers_by_location(start_date, end_date, customer_type),
        use_container_width=True
    )
    create_description_button("location_desc_btn", "location_description")
    if st.session_state.get("location_description", False):
        render_customers_by_location_description()
    
    st.markdown("---")
    
    # Product Analysis
    st.subheader("🛍️ Product Performance")
    st.plotly_chart(
        get_total_sales_by_product(start_date, end_date, customer_type),
        use_container_width=True
    )
    create_description_button("products_desc_btn", "products_description")
    if st.session_state.get("products_description", False):
        render_total_sales_by_product_description()
    
    st.markdown("---")
    
    # Customer Metrics
    st.subheader("📊 Customer Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            get_customer_acquisition_cost(start_date, end_date),
            use_container_width=True
        )
        create_description_button("cac_desc_btn", "cac_description")
        if st.session_state.get("cac_description", False):
            render_customer_acquisition_cost_description()
    
    with col2:
        st.plotly_chart(
            get_customer_lifetime_value(start_date, end_date),
            use_container_width=True
        )
        create_description_button("clv_desc_btn", "clv_description")
        if st.session_state.get("clv_description", False):
            render_customer_lifetime_value_description()
    
    # Retention and Orders Analysis
    st.subheader("📈 Retention & Orders Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            get_customer_retention_rate(start_date, end_date),
            use_container_width=True
        )
        create_description_button("retention_desc_btn", "retention_description")
        if st.session_state.get("retention_description", False):
            render_customer_retention_rate_description()
    
    with col2:
        st.plotly_chart(
            get_total_orders_by_month(start_date, end_date, customer_type),
            use_container_width=True
        )
        create_description_button("orders_month_desc_btn", "orders_month_description")
        if st.session_state.get("orders_month_description", False):
            render_total_orders_by_month_description()
    
    # AOV Over Time
    st.subheader("💰 Average Order Value Over Time")
    st.plotly_chart(
        get_average_order_value_over_time(start_date, end_date, customer_type),
        use_container_width=True
    )
    create_description_button("aov_time_desc_btn", "aov_time_description")
    if st.session_state.get("aov_time_description", False):
        render_average_order_value_over_time_description()
    
    # Revenue Comparison
    st.subheader("📊 Revenue Comparison")
    st.plotly_chart(
        get_revenue_comparison_by_month(start_date, end_date, customer_type),
        use_container_width=True
    )
    create_description_button("revenue_comp_desc_btn", "revenue_comp_description")
    if st.session_state.get("revenue_comp_description", False):
        render_revenue_comparison_by_month_description()
    
    # CAC/CLV Ratio
    st.subheader("⚖️ CAC/CLV Ratio Analysis")
    st.plotly_chart(
        get_cac_clv_ratio_over_time(start_date, end_date),
        use_container_width=True
    )
    create_description_button("cac_clv_ratio_desc_btn", "cac_clv_ratio_description")
    if st.session_state.get("cac_clv_ratio_description", False):
        render_cac_clv_ratio_over_time_description()


def main():
    """Main function to run the Streamlit app"""
    
    # Page configuration
    st.set_page_config(
        page_title="Etsy Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF6B6B;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF6B6B;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<h1 class="main-header">📊 Etsy Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Profit & Loss Statement", "📋 Account Statement"])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_profit_loss_statement()
    
    with tab3:
        render_account_statement()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>📊 Etsy Analytics Dashboard | Powered by Streamlit</p>
            <p>🔄 Auto-refresh every 5 minutes | 📱 Mobile-friendly</p>
        </div>
        """, 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
