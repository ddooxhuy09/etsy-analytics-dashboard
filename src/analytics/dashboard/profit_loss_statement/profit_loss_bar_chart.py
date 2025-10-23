import streamlit as st
import pandas as pd
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from src.analytics.utils.postgres_connection import execute_query_with_cache

def execute_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """Execute SQL query and return DataFrame"""
    return execute_query_with_cache(sql, params, ttl=300)

def get_revenue_expenses_profit_bar_data(start_date: str = None, end_date: str = None, view_mode: str = 'month'):
    """Get Revenue, Operating Expenses, and Profit data for stacked bar chart"""
    
    # Base date filter for all queries
    date_filter = ""
    if start_date:
        date_filter += f" AND dt.full_date >= '{start_date}'"
    if end_date:
        date_filter += f" AND dt.full_date <= '{end_date}'"
    
    
    # Select keys based on view_mode
    if view_mode == 'year':
        key_select = "dt.year"
        key_group_order = "GROUP BY dt.year ORDER BY dt.year"
    elif view_mode == 'month_year':
        # For month/year view: group by year and month
        key_select = "dt.year, dt.month, dt.month_name"
        key_group_order = "GROUP BY dt.year, dt.month, dt.month_name ORDER BY dt.year, dt.month"
    else:
        # For month view: group by month only (aggregate across all years)
        key_select = "dt.month, dt.month_name"
        key_group_order = "GROUP BY dt.month, dt.month_name ORDER BY dt.month"
    
    # Get data with Revenue and Operating Expenses
    sql = f"""
    SELECT 
        {key_select},
        -- Revenue from Sales
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Sale' THEN fft.amount 
            ELSE 0 
        END), 0) as revenue,
        
        -- Operating Expenses (Etsy Fees + VAT)
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Fee' THEN ABS(fft.fees_and_taxes)
            WHEN fft.transaction_type = 'Marketing' THEN ABS(fft.fees_and_taxes)
            WHEN fft.transaction_type = 'VAT' THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as operating_expenses
    
    FROM fact_financial_transactions fft
    JOIN dim_time dt ON fft.transaction_date_key = dt.time_key
    WHERE 1=1 {date_filter}
    {key_group_order}
    """
    
    data = execute_query(sql, None)
    
    if data.empty:
        return pd.DataFrame()
    
    # Don't calculate profit here - it will be calculated using the formula from the table
    # data['profit'] = data['revenue'] - data['operating_expenses']
    
    # Create chart data structure
    chart_data = []
    
    for _, row in data.iterrows():
        if view_mode == 'month':
            period_label = row['month_name']
        elif view_mode == 'month_year':
            period_label = str(row['year']) + ' ' + row['month_name']
        else:
            period_label = str(row['year'])
        
        # Revenue (positive)
        chart_data.append({
            'Period': period_label,
            'Category': 'Revenue',
            'Amount (USD)': row['revenue']
        })
        
        # Operating Expenses (negative, displayed as positive for stacking)
        chart_data.append({
            'Period': period_label,
            'Category': 'Operating Expenses',
            'Amount (USD)': row['operating_expenses']
        })
        
        # Profit will be calculated dynamically using the table formula
        chart_data.append({
            'Period': period_label,
            'Category': 'Profit',
            'Amount (USD)': 0  # Placeholder, will be calculated in the main function
        })
    
    return pd.DataFrame(chart_data)
