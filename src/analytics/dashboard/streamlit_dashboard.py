import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

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

# Database configuration
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "etsy",
    "user": "etsy",
    "password": "etsy"
}


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
            # Both year and month selected - specific month
            # Convert month name to number (subtract 1 because we added "Select Month" at index 0)
            month_number = month_names.index(selected_month)
            
            # First day of the month
            start_date = datetime(selected_year, month_number, 1).date()
            
            # Last day of the month
            if month_number == 12:
                next_month = datetime(selected_year + 1, 1, 1)
            else:
                next_month = datetime(selected_year, month_number + 1, 1)
            
            end_date = (next_month - timedelta(days=1)).date()
            
            # Display the calculated dates
            st.sidebar.info(f"📅 Selected Period: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
        else:
            # Only year selected - entire year
            start_date = datetime(selected_year, 1, 1).date()  # January 1st
            end_date = datetime(selected_year, 12, 31).date()  # December 31st
            
            # Display the calculated dates
            st.sidebar.info(f"📅 Selected Year: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
    else:
        start_date = None
        end_date = None
    
    st.sidebar.markdown("---")
    
    # Manual date range filter (optional)
    st.sidebar.subheader("📅 Manual Date Range (Optional)")
    st.sidebar.caption("Override the month/year selection above")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        manual_start_date = st.date_input("From Date", value=None, key="manual_start_date")
    with col2:
        manual_end_date = st.date_input("To Date", value=None, key="manual_end_date")
    
    # Use manual dates if provided, otherwise use month/year selection
    if manual_start_date or manual_end_date:
        start_date = manual_start_date
        end_date = manual_end_date
        st.sidebar.info("📅 Using manual date selection")
    
    # Customer type filter
    customer_type = st.sidebar.selectbox(
        "Customer Type",
        options=['all', 'new', 'return'],
        format_func=lambda x: {'all': 'All Customers', 'new': 'New Customers', 'return': 'Returning Customers'}[x]
    )
    
    # Customer lifespan for CLV
    customer_lifespan_months = st.sidebar.slider("Customer Lifespan (months)", min_value=1, max_value=60, value=12)
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", type="primary", key="dashboard_refresh"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content
    st.header("📈 Etsy Analytics Dashboard")
    
    # Convert dates to string format
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None
    
    # =============================================================================
    # CORE KPIs SECTION
    # =============================================================================
    st.subheader("📊 Core KPIs")
    
    # Get KPI data
    with st.spinner("Loading KPI data..."):
        total_revenue_data = get_total_revenue(start_date_str, end_date_str, customer_type)
        total_orders_data = get_total_orders(start_date_str, end_date_str, customer_type)
        total_customers_data = get_total_customers(start_date_str, end_date_str, customer_type)
        aov_data = get_average_order_value(start_date_str, end_date_str, customer_type)
    
    # Display KPIs in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"${total_revenue_data.iloc[0, 0]:,.2f}" if not total_revenue_data.empty and total_revenue_data.iloc[0, 0] is not None else "$0.00",
            help="Total revenue after discounts"
        )
        if create_description_button("btn_total_revenue_description", "show_total_revenue_description", "📋", width='content'):
            pass
    
    with col2:
        st.metric(
            label="📦 Total Orders",
            value=f"{total_orders_data.iloc[0, 0]:,}" if not total_orders_data.empty and total_orders_data.iloc[0, 0] is not None else "0",
            help="Total number of orders"
        )
        if create_description_button("btn_total_orders_description", "show_total_orders_description", "📋", width='content'):
            pass
    
    with col3:
        st.metric(
            label="👥 Total Customers",
            value=f"{total_customers_data.iloc[0, 0]:,}" if not total_customers_data.empty and total_customers_data.iloc[0, 0] is not None else "0",
            help="Total number of unique customers"
        )
        if create_description_button("btn_total_customers_description", "show_total_customers_description", "📋", width='content'):
            pass
    
    with col4:
        st.metric(
            label="💵 Average Order Value",
            value=f"${aov_data.iloc[0, 0]:,.2f}" if not aov_data.empty and aov_data.iloc[0, 0] is not None else "$0.00",
            help="Average value per order"
        )
        if create_description_button("btn_average_order_value_description", "show_average_order_value_description", "📋", width='content'):
            pass
    
    # Render KPI descriptions
    render_get_total_revenue_description(start_date_str, end_date_str, customer_type)
    render_get_total_orders_description(start_date_str, end_date_str, customer_type)
    render_get_total_customers_description(start_date_str, end_date_str, customer_type)
    render_get_average_order_value_description(start_date_str, end_date_str, customer_type)
    
    st.markdown("---")
    
    # =============================================================================
    # REVENUE CHARTS SECTION
    # =============================================================================
    st.subheader("💰 Revenue Analytics")
    
    # Revenue by Month Chart
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("📊 Total Revenue by Month")
    
    with col2:
        if create_description_button("btn_revenue_by_month_description", "show_revenue_by_month_description"):
            pass
    
    # Get monthly revenue data
    with st.spinner("Loading monthly revenue data..."):
        monthly_data = get_revenue_by_month(start_date_str, end_date_str, customer_type)
    
    if not monthly_data.empty:
        # Create bar chart
        fig = px.bar(
            monthly_data,
            x='Month',
            y='Revenue (USD)',
            title="Monthly Revenue (USD)",
            labels={'Revenue (USD)': 'Revenue (USD)', 'Month': 'Month'},
            color='Revenue (USD)',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45,
            showlegend=False,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
        )
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No revenue data available for the selected period")
    
    # Render description for revenue by month
    render_revenue_by_month_description(start_date_str, end_date_str, customer_type)
    
    
    
    # Profit by Month Chart (based on fact_payments.net_amount)
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📊 Profit by Month")
    with col2:
        if create_description_button("btn_profit_by_month_description", "show_profit_by_month_description"):
            pass

    with st.spinner("Loading monthly profit data..."):
        profit_monthly = get_profit_by_month(start_date_str, end_date_str, customer_type)

    if not profit_monthly.empty:
        fig = px.bar(
            profit_monthly,
            x='Month',
            y='Profit (USD)',
            title="Monthly Profit (USD)",
            labels={'Profit (USD)': 'Profit (USD)', 'Month': 'Month'},
            color='Profit (USD)',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            height=460,
            xaxis_tickangle=-45,
            showlegend=False,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
        )
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No profit data available for the selected period")

    render_profit_by_month_description(start_date_str, end_date_str, customer_type)


    
    st.markdown("---")
    
    # =============================================================================
    # CUSTOMER ANALYTICS SECTION
    # =============================================================================
    st.subheader("👥 Customer Analytics")
    
    # New vs Returning Customer Sales
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("🎯 New vs Returning Customer Sales")
    
    with col2:
        if create_description_button("btn_new_vs_returning_description", "show_new_vs_returning_customer_sales_description"):
            pass
            pass
    
    with st.spinner("Loading customer sales data..."):
        customer_sales_data = get_new_vs_returning_customer_sales(start_date_str, end_date_str, customer_type)
    
    if not customer_sales_data.empty:
        fig = px.pie(
            customer_sales_data,
            values='Revenue (USD)',
            names='Customer Type',
            title="Revenue by Customer Type (USD)",
            color_discrete_sequence=['#FF6B6B', '#4ECDC4']
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white'
        )
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No customer sales data available for the selected period")
    
    # Render description for new vs returning customer sales
    render_new_vs_returning_customer_sales_description(start_date_str, end_date_str, customer_type)
    
    # New Customers Over Time
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("👥 New Customers Over Time")
    
    with col2:
        if create_description_button("btn_new_customers_over_time_description", "show_new_customers_over_time_description"):
            pass
            pass
    
    with st.spinner("Loading new customers data..."):
        new_customers_data = get_new_customers_over_time(start_date_str, end_date_str, customer_type)
    
    if not new_customers_data.empty:
        fig = px.line(
            new_customers_data,
            x='Date',
            y='New Customers',
            title="New Customers Over Time",
            color_discrete_sequence=['#FFA726']
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
        )
        fig.update_traces(line=dict(width=3), marker=dict(size=6))
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No new customers data available for the selected period")
    
    # Render description for new customers over time
    render_new_customers_over_time_description(start_date_str, end_date_str, customer_type)
    
    # Customers by Location
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("🌍 Customers by Location (US States)")
    
    with col2:
        if create_description_button("btn_customers_by_location_description", "show_customers_by_location_description"):
            pass
            pass
    
    with st.spinner("Loading location data..."):
        location_data = get_customers_by_location(start_date_str, end_date_str, customer_type)
    
    if not location_data.empty:
        fig = px.bar(
            location_data,
            x='State',
            y='Customers',
            title="Customers by US State",
            labels={'Customers': 'Number of Customers', 'State': 'US State'},
            color='Customers',
            color_continuous_scale='Plasma'
        )
        fig.update_layout(
            height=400, 
            xaxis_tickangle=-45,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
        )
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No location data available for the selected period")
    
    # Render description for customers by location
    render_customers_by_location_description(start_date_str, end_date_str, customer_type)
    
    # Move Retention Rate up under Customer Analytics
    col1, col2 = st.columns(2)
    with col2:
        st.subheader("🔄 Customer Retention Rate")
        if create_description_button("btn_retention_rate_description", "show_retention_rate_description"):
            pass
        with st.spinner("Loading retention rate data..."):
            retention_rate_data = get_customer_retention_rate(start_date_str, end_date_str, customer_type)
        if not retention_rate_data.empty:
            st.metric(
                label="Retention Rate (%)",
                value=f"{retention_rate_data.iloc[0, 0]:.2f}%" if retention_rate_data.iloc[0, 0] is not None else "0.00%",
                help="Percentage of customers who made repeat purchases"
            )
        else:
            st.info("No retention rate data available")
        render_customer_retention_rate_description(start_date_str, end_date_str, customer_type)
    
    st.markdown("---")
    
    # =============================================================================
    # PRODUCT ANALYTICS SECTION
    # =============================================================================
    st.subheader("🏆 Product Analytics")
    
    # Total Sales by Product
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("🏆 Top 10 Products by Revenue")
    
    with col2:
        if create_description_button("btn_total_sales_by_product_description", "show_total_sales_by_product_description"):
            pass
            pass
    
    with st.spinner("Loading product sales data..."):
        product_sales_data = get_total_sales_by_product(start_date_str, end_date_str, customer_type)
    
    if not product_sales_data.empty:
        fig = px.bar(
            product_sales_data,
            x='Revenue (USD)',
            y='Product',
            title="Top 10 Products by Revenue (USD)",
            orientation='h',
            labels={'Revenue (USD)': 'Revenue (USD)', 'Product': 'Product Name'},
            color='Revenue (USD)',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            height=500,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
        )
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No product sales data available for the selected period")
    
    # Render description for total sales by product
    render_total_sales_by_product_description(start_date_str, end_date_str, customer_type)
    
    st.markdown("---")
    
    # =============================================================================
    # FINANCIAL ANALYTICS SECTION
    # =============================================================================
    st.subheader("💳 Financial Analytics")
    
    # CAC and CLV
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧲 Customer Acquisition Cost (CAC)")
        if create_description_button("btn_cac_description", "show_customer_acquisition_cost_description"):
            pass
            pass
        
        with st.spinner("Loading CAC data..."):
            cac_data = get_customer_acquisition_cost(start_date_str, end_date_str)
        
        if not cac_data.empty:
            st.metric(
                label="CAC (USD)",
                value=f"${cac_data.iloc[0, 0]:,.2f}" if cac_data.iloc[0, 0] is not None else "$0.00",
                help="Cost to acquire one new customer"
            )
        else:
            st.info("No CAC data available")
        
        # Render description for customer acquisition cost
        render_customer_acquisition_cost_description(start_date_str, end_date_str, customer_type)
    
    with col2:
        st.subheader("💎 Customer Lifetime Value (CLV)")
        if create_description_button("btn_clv_description", "show_customer_lifetime_value_description"):
            pass
            pass
        
        with st.spinner("Loading CLV data..."):
            clv_data = get_customer_lifetime_value(start_date_str, end_date_str, customer_type, customer_lifespan_months)
        
        if not clv_data.empty:
            st.metric(
                label="CLV (USD)",
                value=f"${clv_data.iloc[0, 0]:,.2f}" if clv_data.iloc[0, 0] is not None else "$0.00",
                help="Lifetime value of a customer"
            )
        else:
            st.info("No CLV data available")
        
        # Render description for customer lifetime value
        render_customer_lifetime_value_description(start_date_str, end_date_str, customer_type)

    # Move CAC/CLV Ratio section here for Financial Analytics
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📊 Monthly CAC vs CLV with CLV/CAC Ratio")
    with col2:
        if create_description_button("btn_cac_clv_ratio_description", "show_cac_clv_ratio_description"):
            pass

    with st.spinner("Loading CAC/CLV ratio data..."):
        cac_clv_df = get_cac_clv_ratio_over_time(start_date_str, end_date_str, customer_lifespan_months)

    if not cac_clv_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cac_clv_df['Month'], y=cac_clv_df['CAC (USD)'], name='CAC (USD)', marker_color='#9C27B0'))
        fig.add_trace(go.Bar(x=cac_clv_df['Month'], y=cac_clv_df['CLV (USD)'], name='CLV (USD)', marker_color='#00BCD4'))
        fig.add_trace(go.Scatter(x=cac_clv_df['Month'], y=cac_clv_df['CLV/CAC (x)'], name='CLV/CAC (x)', mode='lines+markers', yaxis='y2', line=dict(color='#FFA726', width=3)))

        fig.update_layout(
            title="Monthly CAC vs CLV with CLV/CAC Ratio",
            barmode='group',
            height=500,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(title='USD', color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis2=dict(title='CLV/CAC (x)', overlaying='y', side='right', color='white', gridcolor='rgba(255,255,255,0.2)', tickformat='.1f', tickprefix='', ticksuffix='x'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No CAC/CLV ratio data available for the selected period")

    render_cac_clv_ratio_over_time_description(start_date_str, end_date_str)
    
    st.markdown("---")
    
    # =============================================================================
    # ORDER ANALYTICS SECTION
    # =============================================================================
    st.subheader("📦 Order Analytics")
    
    # Total Orders by Month
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("📦 Total Orders by Month")
    
    with col2:
        if create_description_button("btn_total_orders_by_month_description", "show_total_orders_by_month_description"):
            pass
    
    with st.spinner("Loading orders by month data..."):
        orders_by_month_data = get_total_orders_by_month(start_date_str, end_date_str, customer_type)
    
    if not orders_by_month_data.empty:
        fig = px.bar(
            orders_by_month_data,
            x='Month',
            y='Orders',
            title="Total Orders by Month",
            labels={'Orders': 'Number of Orders', 'Month': 'Month'},
            color='Orders',
            color_continuous_scale='Greens'
        )
        fig.update_layout(
            height=400, 
            xaxis_tickangle=-45,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
        )
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No orders by month data available for the selected period")
    
    # Render description for total orders by month
    render_total_orders_by_month_description(start_date_str, end_date_str, customer_type)
    
    # Average Order Value Over Time
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("📊 Average Order Value Over Time")
    
    with col2:
        if create_description_button("btn_aov_over_time_description", "show_average_order_value_over_time_description"):
            pass
    
    with st.spinner("Loading AOV over time data..."):
        aov_over_time_data = get_average_order_value_over_time(start_date_str, end_date_str, customer_type)
    
    if not aov_over_time_data.empty:
        fig = px.line(
            aov_over_time_data,
            x='Date',
            y='AOV (USD)',
            title="Average Order Value Over Time (USD)",
            color_discrete_sequence=['#FF5722']
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)')
        )
        fig.update_traces(line=dict(width=3))
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
    else:
        st.info("No AOV over time data available for the selected period")
    
    # Render description for average order value over time
    render_average_order_value_over_time_description(start_date_str, end_date_str, customer_type)
    
    
    
    st.markdown("---")
    
    # =============================================================================
    # REVENUE COMPARISON SECTION
    # =============================================================================
    st.subheader("📊 Revenue Comparison")
    
    # Revenue Comparison by Month
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.subheader("📈 Revenue Comparison by Month")
    
    with col2:
        if create_description_button("btn_revenue_comparison_description", "show_revenue_comparison_by_month_description"):
            pass
    
    # Comparison filters (separate from main dashboard filters)
    st.subheader("🔍 Comparison Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        month1_year = st.selectbox(
            "Month 1 - Year",
            options=list(range(2020, datetime.now().year + 2)),
            index=datetime.now().year - 2020,
            key="month1_year"
        )
    
    with col2:
        month1_month = st.selectbox(
            "Month 1 - Month",
            options=list(range(1, 13)),
            format_func=lambda x: get_month_name(x),
            key="month1_month"
        )
    
    with col3:
        month2_year = st.selectbox(
            "Month 2 - Year",
            options=list(range(2020, datetime.now().year + 2)),
            index=datetime.now().year - 2021,  # Default to previous year
            key="month2_year"
        )
    
    with col4:
        month2_month = st.selectbox(
            "Month 2 - Month",
            options=list(range(1, 13)),
            format_func=lambda x: get_month_name(x),
            key="month2_month"
        )
    
    # Display comparison period
    month1_name = get_month_name(month1_month)
    month2_name = get_month_name(month2_month)
    st.info(f"📅 Comparing: {month1_name} {month1_year} vs {month2_name} {month2_year}")
    
    # Get comparison data
    with st.spinner("Loading revenue comparison data..."):
        comparison_data = get_revenue_comparison_by_month(month1_year, month1_month, month2_year, month2_month)
    
    if not comparison_data.empty:
        # Create line chart for daily comparison
        fig = go.Figure()
        
        # Add line for Month 1
        month1_data = comparison_data[comparison_data['Month'] == 'Month 1'].sort_values('Day')
        if not month1_data.empty:
            fig.add_trace(go.Scatter(
                x=month1_data['Day'],
                y=month1_data['Revenue (USD)'],
                mode='lines+markers',
                name=f"{month1_name} {month1_year}",
                line=dict(color='#FF6B6B', width=3),
                marker=dict(size=6)
            ))
        
        # Add line for Month 2
        month2_data = comparison_data[comparison_data['Month'] == 'Month 2'].sort_values('Day')
        if not month2_data.empty:
            fig.add_trace(go.Scatter(
                x=month2_data['Day'],
                y=month2_data['Revenue (USD)'],
                mode='lines+markers',
                name=f"{month2_name} {month2_year}",
                line=dict(color='#4ECDC4', width=3),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="Daily Revenue Comparison by Month (USD)",
            xaxis_title="Day of Month",
            yaxis_title="Revenue (USD)",
            height=500,
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.2)'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
        
        # Display comparison metrics
        if not month1_data.empty and not month2_data.empty:
            month1_total = month1_data['Revenue (USD)'].sum()
            month2_total = month2_data['Revenue (USD)'].sum()

            # Compute Order Total %, Revenue %, Profit % using helper
            from src.analytics.dashboard.charts.get_revenue_comparison_by_month import get_comparison_percentages
            cmp = get_comparison_percentages(month1_year, month1_month, month2_year, month2_month)

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric(
                    label=f"{month1_name} {month1_year} Total",
                    value=f"${month1_total:,.2f}",
                    help=f"Total revenue for {month1_name} {month1_year}"
                )

            with col2:
                st.metric(
                    label=f"{month2_name} {month2_year} Total",
                    value=f"${month2_total:,.2f}",
                    help=f"Total revenue for {month2_name} {month2_year}"
                )

            with col3:
                val = cmp.get("orders_pct")
                st.metric(
                    label="Order Total %",
                    value=f"{val:.1f}%" if val is not None else "N/A",
                    help="(Orders in M1 / Orders in M2) * 100"
                )

            with col4:
                val = cmp.get("revenue_pct")
                st.metric(
                    label="Revenue %",
                    value=f"{val:.1f}%" if val is not None else "N/A",
                    help="(Revenue in M1 / Revenue in M2) * 100"
                )

            with col5:
                val = cmp.get("profit_pct")
                st.metric(
                    label="Profit %",
                    value=f"{val:.1f}%" if val is not None else "N/A",
                    help="(Profit in M1 / Profit in M2) * 100"
                )
    else:
        st.info("No comparison data available for the selected months")
    
    # Render description for revenue comparison
    render_revenue_comparison_by_month_description(month1_year, month1_month, month2_year, month2_month)
    
    st.markdown("---")

