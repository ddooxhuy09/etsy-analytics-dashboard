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

def get_profit_loss_line_chart_data(start_date: str = None, end_date: str = None, view_mode: str = 'month'):
    """Get Profit and Loss line chart data for plotting trends"""
    
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
        key_label = "year"
    elif view_mode == 'month_year':
        # For month/year view: group by year and month
        key_select = "dt.year, dt.month, dt.month_name"
        key_group_order = "GROUP BY dt.year, dt.month, dt.month_name ORDER BY dt.year, dt.month"
        key_label = "month_year"
    else:
        # For month view: group by month only (aggregate across all years)
        key_select = "dt.month, dt.month_name"
        key_group_order = "GROUP BY dt.month, dt.month_name ORDER BY dt.month"
        key_label = "month"
    
    # Get data with all components (same query as table)
    monthly_pl_sql = f"""
    SELECT 
        {key_select},
        -- Revenue from Sales
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Sale' THEN fft.amount 
            ELSE 0 
        END), 0) as revenue,
        
        -- Refund Cost
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Refund' THEN ABS(fft.amount) 
            ELSE 0 
        END), 0) as refund_cost,
        
        -- Transaction Fee
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Fee' 
                AND (fft.transaction_title ILIKE '%Transaction fee%' OR fft.transaction_title ILIKE '%transaction fee%')
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as transaction_fee,
        
        -- Processing Fee
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Fee' 
                AND (fft.transaction_title ILIKE '%Processing fee%' OR fft.transaction_title ILIKE '%processing fee%')
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as processing_fee,
        
        -- Regulatory Operating Fee
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Fee' 
                AND fft.transaction_title ILIKE '%Regulatory Operating fee%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as regulatory_fee,
        
        -- Listing Fee
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Fee' 
                AND (fft.transaction_title ILIKE '%Listing fee%' OR fft.transaction_title ILIKE '%listing fee%')
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as listing_fee,
        
        -- Marketing Fee
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'Marketing'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as marketing_fee,
        
        -- VAT Fees breakdown
        -- auto-renew sold
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'VAT' 
                AND fft.transaction_title ILIKE '%auto-renew sold%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as vat_auto_renew_sold,
        
        -- shipping_transaction
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'VAT' 
                AND fft.transaction_title ILIKE '%shipping_transaction%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as vat_shipping_transaction,
        
        -- Processing Fee
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'VAT' 
                AND fft.transaction_title ILIKE '%Processing Fee%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as vat_processing_fee,
        
        -- transaction credit
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'VAT' 
                AND fft.transaction_title ILIKE '%transaction credit%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as vat_transaction_credit,
        
        -- listing credit
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'VAT' 
                AND fft.transaction_title ILIKE '%listing credit%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as vat_listing_credit,
        
        -- listing
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'VAT' 
                AND fft.transaction_title ILIKE '%listing%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as vat_listing,
        
        -- Etsy Plus subscription
        COALESCE(SUM(CASE 
            WHEN fft.transaction_type = 'VAT' 
                AND fft.transaction_title ILIKE '%Etsy Plus subscription%'
            THEN ABS(fft.fees_and_taxes)
            ELSE 0 
        END), 0) as vat_etsy_plus_subscription
    
    FROM fact_financial_transactions fft
    JOIN dim_time dt ON fft.transaction_date_key = dt.time_key
    WHERE 1=1 {date_filter}
    {key_group_order}
    """
    
    monthly_data = execute_query(monthly_pl_sql, None)
    
    if monthly_data.empty:
        return pd.DataFrame()
    
    # Calculate derived fields
    monthly_data['total_etsy_fees'] = (monthly_data['transaction_fee'] + 
                                     monthly_data['processing_fee'] + 
                                     monthly_data['regulatory_fee'] + 
                                     monthly_data['listing_fee'] +
                                     monthly_data['marketing_fee'])
    
    # Calculate total VAT fees
    monthly_data['total_vat_fees'] = (monthly_data['vat_auto_renew_sold'] + 
                                    monthly_data['vat_shipping_transaction'] + 
                                    monthly_data['vat_processing_fee'] + 
                                    monthly_data['vat_transaction_credit'] + 
                                    monthly_data['vat_listing_credit'] + 
                                    monthly_data['vat_listing'] + 
                                    monthly_data['vat_etsy_plus_subscription'])
    
    # Calculate Cost of Goods from fact_bank_transactions
    cogs_sql = f"""
    SELECT 
        {key_select},
        COALESCE(SUM(fbt.debit_amount), 0) as cost_of_goods
    FROM fact_bank_transactions fbt
    JOIN dim_time dt ON fbt.transaction_date_key = dt.time_key
    WHERE 1=1 {date_filter}
    {key_group_order}
    """
    
    cogs_data = execute_query(cogs_sql, None)
    
    # Merge cost of goods data with main data
    if not cogs_data.empty:
        # Merge based on the grouping keys
        if view_mode == 'year':
            merge_cols = ['year']
        elif view_mode == 'month_year':
            merge_cols = ['year', 'month', 'month_name']
        else:
            merge_cols = ['month', 'month_name']
        
        monthly_data = monthly_data.merge(cogs_data, on=merge_cols, how='left')
        monthly_data['cost_of_goods'] = monthly_data['cost_of_goods'].fillna(0)
    else:
        monthly_data['cost_of_goods'] = 0
    
    monthly_data['net_profit'] = 0     # Empty as requested
    
    # Create line chart data structure
    chart_data = []
    
    # Define line items for chart (matching the table structure)
    line_items = [
        ('Revenue', 'revenue'),
        ('Refund Cost', 'refund_cost'),
        ('Cost of Goods', 'cost_of_goods'),
        ('Etsy Fees', 'total_etsy_fees'),
        ('  - Transaction Fee', 'transaction_fee'),
        ('  - Processing Fee', 'processing_fee'),
        ('  - Regulatory Operating Fee', 'regulatory_fee'),
        ('  - Listing Fee', 'listing_fee'),
        ('  - Marketing', 'marketing_fee'),
        ('  - VAT', 'total_vat_fees'),
        ('    --- auto-renew sold', 'vat_auto_renew_sold'),
        ('    --- shipping_transaction', 'vat_shipping_transaction'),
        ('    --- Processing Fee', 'vat_processing_fee'),
        ('    --- transaction credit', 'vat_transaction_credit'),
        ('    --- listing credit', 'vat_listing_credit'),
        ('    --- listing', 'vat_listing'),
        ('    --- Etsy Plus subscription', 'vat_etsy_plus_subscription')
    ]
    
    for line_item, column_name in line_items:
        # Group by period and sum values to ensure only one value per period per line item
        if view_mode == 'month':
            # For monthly view, group by month only (aggregate across all years)
            period_values = monthly_data.groupby(['month', 'month_name'])[column_name].sum().reset_index()
            period_values = period_values.sort_values(['month'])
        elif view_mode == 'month_year':
            # For month/year view, use year and month directly
            period_values = monthly_data.groupby(['year', 'month', 'month_name'])[column_name].sum().reset_index()
            period_values = period_values.sort_values(['year', 'month'])
        else:
            # For yearly view, use year directly
            period_values = monthly_data.groupby('year')[column_name].sum().reset_index()
            period_values['year_str'] = period_values['year'].astype(str)
        
        for _, period_row in period_values.iterrows():
            if view_mode == 'month':
                period_label = period_row['month_name']
            elif view_mode == 'month_year':
                period_label = str(period_row['year']) + ' ' + period_row['month_name']
            else:
                period_label = period_row['year_str']
            value = period_row[column_name]
            
            chart_data.append({
                'Period': period_label,
                'Line Item': line_item,
                'Amount (USD)': value
            })
    
    return pd.DataFrame(chart_data)
