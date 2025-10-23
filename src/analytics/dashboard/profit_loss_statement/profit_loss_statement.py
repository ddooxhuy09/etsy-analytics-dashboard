import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import textwrap

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from src.analytics.dashboard.profit_loss_statement.profit_loss_summary_table import get_profit_loss_summary_table, render_profit_loss_summary_table_description
from src.analytics.dashboard.profit_loss_statement.profit_loss_line_chart import get_profit_loss_line_chart_data
from src.analytics.dashboard.profit_loss_statement.profit_loss_bar_chart import get_revenue_expenses_profit_bar_data

def create_description_button(button_key, description_key, text="📋 Show Description", width='stretch'):
    """Create a description button with proper callback"""
    if st.button(text, key=button_key, width=width):
        st.session_state[description_key] = not st.session_state.get(description_key, False)
        st.rerun()
    return False

def render_profit_loss_statement(start_date_str=None, end_date_str=None, customer_type=None):
    """Render the complete Profit & Loss Statement tab"""
    
    st.header("💰 Profit & Loss Statement")
    
    # =============================================================================
    # USE SHARED DASHBOARD FILTERS
    # =============================================================================
    
    # Get filter values from session state (shared with main dashboard)
    selected_year = st.session_state.get("selected_year", "Select Year")
    selected_month = st.session_state.get("selected_month", "Select Month")
    manual_start_date = st.session_state.get("manual_start_date", None)
    manual_end_date = st.session_state.get("manual_end_date", None)
    
    # Calculate dates using same logic as main dashboard
    if selected_year != "Select Year":
        if selected_month != "Select Month":
            # Both year and month selected - specific month
            month_names = [
                "Select Month", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            month_number = month_names.index(selected_month)
            
            # First day of the month
            start_date = datetime(selected_year, month_number, 1).date()
            
            # Last day of the month
            if month_number == 12:
                next_month = datetime(selected_year + 1, 1, 1)
            else:
                next_month = datetime(selected_year, month_number + 1, 1)
            
            end_date = (next_month - timedelta(days=1)).date()
        else:
            # Only year selected - entire year
            start_date = datetime(selected_year, 1, 1).date()  # January 1st
            end_date = datetime(selected_year, 12, 31).date()  # December 31st
    else:
        start_date = None
        end_date = None
    
    # Use manual dates if provided, otherwise use month/year selection
    if manual_start_date or manual_end_date:
        start_date = manual_start_date
        end_date = manual_end_date
    
    # Set default customer type to 'all'
    customer_type = 'all'
    
    # Convert dates to string format
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None
    
    # =============================================================================
    # PROFIT & LOSS SUMMARY TABLE SECTION
    # =============================================================================
    
    # Profit & Loss Summary Table
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader("📊 Profit & Loss Summary Table")
    with col2:
        view_mode = st.selectbox("View", options=["Month", "Year", "Month/Year"], index=0, key="pl_view_mode")
    with col3:
        if st.button("📋 Show Description", key="btn_pl_summary_description", width='stretch'):
            st.session_state.show_profit_loss_summary_table_description = not st.session_state.get('show_profit_loss_summary_table_description', False)
            st.rerun()

    # Use the same dashboard-level date filters (start_date_str, end_date_str)
    with st.spinner("Loading Profit & Loss data..."):
        if view_mode == 'Year':
            view_mode_param = 'year'
        elif view_mode == 'Month/Year':
            view_mode_param = 'month_year'
        else:
            view_mode_param = 'month'
        pl_data = get_profit_loss_summary_table(start_date_str, end_date_str, view_mode=view_mode_param)

    if not pl_data.empty:
        # Initialize session state for selected items
        if 'profit_formula_items' not in st.session_state:
            st.session_state.profit_formula_items = ['Revenue']
        
        # Get available line items (excluding empty ones and header rows)
        available_items = pl_data[pl_data['Line Item'].notna()]['Line Item'].tolist()
        
        # Remove header rows from available items
        header_rows_to_exclude = [
            'Revenue (Sales)',
            '',
            'COGS (Cost of Goods Sold)',
            'Operating Expenses',
            'Net Income (Profit)'
        ]
        available_items = [item for item in available_items if item not in header_rows_to_exclude]
        
        # Define parent-child relationships for selection constraints
        etsy_fees_children = [
            '  - Transaction Fee',
            '  - Processing Fee',
            '  - Regulatory Operating Fee',
            '  - Listing Fee',
            '  - Marketing',
            '  - VAT'
        ]
        vat_children = [
            '    --- auto-renew sold',
            '    --- shipping_transaction',
            '    --- Processing Fee',
            '    --- transaction credit',
            '    --- listing credit',
            '    --- listing',
            '    --- Etsy Plus subscription'
        ]
        cogs_children = [
            '  - Chi phí len (Chi phí nguyên liệu, vật liệu trực tiếp)',
            '  - Chi phí làm concept design (Chi phí nhân công trực tiếp)',
            '  - Chi phí làm chart + móc + quay (optional) (Chi phí nhân công trực tiếp)',
            '  - Chi phí quay (Chi phí nhân công trực tiếp)',
            '  - Chi phí chụp + quay (Chi phí nhân công trực tiếp)',
            '  - Chi phí viết pattern - dịch chart (Chi phí nhân công trực tiếp)'
        ]
        
        # Calculate profit values and update table
        if st.session_state.profit_formula_items:
            # Calculate profit for each month and Full Year
            numeric_columns = [col for col in pl_data.columns if col != 'Line Item']
            profit_values = {}
            
            for col in numeric_columns:
                profit_value = 0
                for item in st.session_state.profit_formula_items:
                    item_row = pl_data[pl_data['Line Item'] == item].index
                    if not item_row.empty:
                        item_value = pl_data.loc[item_row[0], col]
                        if item == 'Revenue':
                            profit_value += item_value
                        else:
                            profit_value -= item_value
                profit_values[col] = profit_value
            
            # Update Profit row in the table
            profit_row_idx = pl_data[pl_data['Line Item'] == 'Profit'].index
            if not profit_row_idx.empty:
                for col in numeric_columns:
                    pl_data.loc[profit_row_idx[0], col] = profit_values[col]
        
        # Display the table with updated profit values using Pandas Styler (inline CSS) to reliably reduce font size
        numeric_cols_for_style = [col for col in pl_data.columns if col != 'Line Item']
        # Ensure rounding to 2 decimals for display
        pl_data[numeric_cols_for_style] = pl_data[numeric_cols_for_style].round(2)
        # Remove the default pandas index to avoid a left-most order/index column
        pl_data = pl_data.reset_index(drop=True)
        
        # Identify category header rows
        header_rows = set([
            'Revenue (Sales)',
            '',
            'COGS (Cost of Goods Sold)',
            'Operating Expenses',
            'Net Income (Profit)'
        ])
        
        # Parent/child relationships for collapsible rows inside the table
        collapsible_parents = {
            'Etsy Fees': etsy_fees_children,
            '  - VAT': [
                '    --- auto-renew sold',
                '    --- shipping_transaction',
                '    --- Processing Fee',
                '    --- transaction credit',
                '    --- listing credit',
                '    --- listing',
                '    --- Etsy Plus subscription'
            ],
            'Cost of Goods': cogs_children
        }

        # Create HTML table with colspan for header rows and horizontal scroll container
        final_html = '<div class="table-container">\n<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">\n'
        
        # Add header row
        final_html += '<thead><tr>\n'
        for col in pl_data.columns:
            final_html += f'<th style="border: 1px solid #555; padding: 8px; font-size: 11px; background-color: #333; color: white;">{col}</th>\n'
        final_html += '</tr></thead>\n'
        
        # Add body rows
        final_html += '<tbody>\n'
        for idx, row in pl_data.iterrows():
            line_item = row['Line Item']
            if line_item in header_rows:
                # Header row with colspan
                final_html += '<tr>\n'
                final_html += f'<td colspan="{len(pl_data.columns)}" style="font-weight: 700; font-size: 15px; padding: 12px 8px; background-color: #444 !important; color: white !important; border: 1px solid #555;">{line_item}</td>\n'
                final_html += '</tr>\n'
            else:
                # Regular data row
                # Determine row classes for collapsible behavior
                row_classes = []
                row_style_overrides = []
                # Children of Etsy Fees (including '  - VAT') should be hidden initially
                if line_item in collapsible_parents.get('Etsy Fees', []):
                    row_classes.append('child-of-etsy-fees')
                    row_style_overrides.append('display: none;')
                # Children of VAT should also be hidden initially
                if line_item in collapsible_parents.get('  - VAT', []):
                    row_classes.append('child-of-vat')
                    row_style_overrides.append('display: none;')
                # Children of COGS should be hidden initially
                if line_item in collapsible_parents.get('Cost of Goods', []):
                    row_classes.append('child-of-cogs')
                    row_style_overrides.append('display: none;')

                tr_class_attr = f" class=\"{' '.join(row_classes)}\"" if row_classes else ''
                tr_style_attr = f" style=\"{' '.join(row_style_overrides)}\"" if row_style_overrides else ''

                final_html += f'<tr{tr_class_attr}{tr_style_attr}>\n'
                for col in pl_data.columns:
                    value = row[col]
                    if value is pd.NA or (isinstance(value, float) and pd.isna(value)):
                        display_value = ""
                        style = "padding: 8px; border: 1px solid #555; color: white; background-color: #222;"
                    elif col == 'Line Item':
                        display_value = str(value)
                        style = "font-size: 12px; padding: 8px; border: 1px solid #555; text-align: left; color: white; background-color: #222;"
                        # Add toggle caret for collapsible parents
                        if display_value in collapsible_parents:
                            # Unique ids per parent
                            if display_value == 'Etsy Fees':
                                toggle_target_class = 'child-of-etsy-fees'
                                toggle_id = 'toggle-etsy-fees'
                            elif display_value == '  - VAT':
                                toggle_target_class = 'child-of-vat'
                                toggle_id = 'toggle-vat'
                            elif display_value == 'Cost of Goods':
                                toggle_target_class = 'child-of-cogs'
                                toggle_id = 'toggle-cogs'
                            else:
                                toggle_target_class = 'child-of-vat'
                                toggle_id = 'toggle-vat'
                            display_value = (
                                f'<span id="{toggle_id}" class="caret collapsed" '
                                f'onclick="toggleGroup(\'{toggle_target_class}\', \'{toggle_id}\')">▸</span> '
                                f'{display_value}'
                            )
                    else:
                        try:
                            display_value = f"{float(value):,.2f}" if float(value) != 0 else "0.00"
                        except (ValueError, TypeError):
                            display_value = str(value) if value else ""
                        style = "font-size: 14px; padding: 8px; border: 1px solid #555; text-align: right; color: white; background-color: #222;"
                    
                    final_html += f'<td style="{style}">{display_value}</td>\n'
                final_html += '</tr>\n'
        
        final_html += '</tbody>\n'
        final_html += '</table>\n</div>'
        
        # Add CSS and JS to ensure proper colors and collapsible behavior
        css_style = """
        <style>
        .table-container {
            overflow-x: auto !important;
            overflow-y: visible !important;
            width: 100%;
            max-width: 100%;
        }
        table {
            background-color: #222 !important;
            color: white !important;
            min-width: 100% !important;
            width: max-content !important;
            border-collapse: collapse !important;
        }
        table th {
            background-color: #333 !important;
            color: white !important;
            padding: 8px !important;
            white-space: nowrap !important;
        }
        table td {
            background-color: #222 !important;
            color: white !important;
            padding: 8px !important;
            white-space: nowrap !important;
        }
        /* Specific styling for header rows */
        table td[colspan] {
            background-color: #444 !important;
            color: white !important;
            font-weight: 700 !important;
            padding: 12px 8px !important;
        }
        /* Caret styling for collapsible parents */
        .caret {
            cursor: pointer;
            user-select: none;
            margin-right: 6px;
            display: inline-block;
            transition: transform 0.15s ease-in-out;
        }
        .caret.expanded { transform: rotate(90deg); }
        .caret.collapsed { transform: rotate(0deg); }
        /* Ensure container allows horizontal scrolling */
        .stApp {
            overflow-x: auto !important;
            overflow-y: visible !important;
        }
        /* Remove any height restrictions */
        div[data-testid="stHorizontalBlock"] {
            overflow: visible !important;
        }
        /* Force horizontal scroll for wide tables */
        .streamlit-container {
            overflow-x: auto !important;
        }
        </style>
        """

        js_code = """
        <script>
        function toggleGroup(groupClass, toggleId) {
            var rows = document.getElementsByClassName(groupClass);
            var toggle = document.getElementById(toggleId);
            var willShow = true;
            // Determine current state: if any row is visible, we'll hide; else show
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].style.display !== 'none') { willShow = false; break; }
            }
            for (var j = 0; j < rows.length; j++) {
                rows[j].style.display = willShow ? '' : 'none';
            }
            if (toggle) {
                toggle.classList.remove(willShow ? 'collapsed' : 'expanded');
                toggle.classList.add(willShow ? 'expanded' : 'collapsed');
            }
        }
        </script>
        """
        
        # Render the HTML table with CSS using components
        try:
            import streamlit.components.v1 as components
            # Calculate dynamic height based on number of rows
            num_rows = len(pl_data)
            dynamic_height = max(400, num_rows * 35 + 100)  # 35px per row + 100px for headers
            components.html(css_style + final_html + js_code, height=dynamic_height, scrolling=True)
        except:
            # Fallback to markdown if components not available
            st.markdown(css_style + final_html + js_code, unsafe_allow_html=True)
        
        # Display formula
        st.markdown("---")
        if st.session_state.profit_formula_items:
            formula_parts = []
            for item in st.session_state.profit_formula_items:
                # Normalize child labels by stripping leading hyphen/indent for display
                display_item = item.lstrip()
                if display_item.startswith('- '):
                    display_item = display_item[2:]
                if display_item.startswith('-'):
                    display_item = display_item[1:].lstrip()
                
                if item == 'Revenue':
                    formula_parts.append(display_item)
                else:
                    formula_parts.append(f"- {display_item}")
            
            formula = " + ".join(formula_parts).replace(" + -", " - ")
            st.markdown(f"**Profit = {formula}**")
        else:
            st.markdown("**Profit = (No items selected)**")
        
        # Show multiselect directly
        st.markdown("**Select items for profit formula:**")
        
        # Multi-select for items not already in formula
        available_to_add = [item for item in available_items if item not in st.session_state.profit_formula_items]
        
        # If any child of Etsy Fees is selected, exclude parent 'Etsy Fees' from options
        has_etsy_child_selected = any(child in st.session_state.profit_formula_items for child in etsy_fees_children)
        if has_etsy_child_selected and 'Etsy Fees' in available_to_add:
            available_to_add.remove('Etsy Fees')
        
        # If any child of VAT is selected, exclude parent '  - VAT' from options
        has_vat_child_selected = any(child in st.session_state.profit_formula_items for child in vat_children)
        if has_vat_child_selected and '  - VAT' in available_to_add:
            available_to_add.remove('  - VAT')
        
        if available_to_add:
            selected_to_add = st.multiselect(
                "Available items:",
                options=available_to_add,
                key="items_to_add_selector"
            )
            
            if st.button("Add Selected Items", key="confirm_add_items"):
                # Before adding, if selecting any Etsy child, remove parent if present
                if any(item in etsy_fees_children for item in selected_to_add):
                    if 'Etsy Fees' in st.session_state.profit_formula_items:
                        st.session_state.profit_formula_items.remove('Etsy Fees')
                # Before adding, if selecting any VAT child, remove parent if present
                if any(item in vat_children for item in selected_to_add):
                    if '  - VAT' in st.session_state.profit_formula_items:
                        st.session_state.profit_formula_items.remove('  - VAT')
                
                # Also, if user somehow selected parent while children already present (should be filtered), ignore parent
                cleaned_to_add = [item for item in selected_to_add if not (
                    (item == 'Etsy Fees' and has_etsy_child_selected) or (item == '  - VAT' and has_vat_child_selected)
                )]
                
                st.session_state.profit_formula_items.extend(cleaned_to_add)
                st.rerun()
        else:
            st.info("All items are already in the formula")
        
        # Remove items UI
        st.markdown("**Remove items from formula:**")
        # Exclude mandatory 'Revenue' from removal to keep formula structure sane
        removable_items = [it for it in st.session_state.profit_formula_items if it != 'Revenue']
        if removable_items:
            selected_to_remove = st.multiselect(
                "Selected items:",
                options=removable_items,
                key="items_to_remove_selector"
            )
            if st.button("Remove Selected Items", key="confirm_remove_items"):
                # If removing all children of a parent, allow parent to be re-added next time (handled by available_to_add calc)
                st.session_state.profit_formula_items = [it for it in st.session_state.profit_formula_items if it not in selected_to_remove]
                st.rerun()
        else:
            st.caption("No removable items in formula")

    if not pl_data.empty:
        # Calculate totals for key metrics (use Full Year column if available, otherwise sum all columns)
        numeric_columns = [col for col in pl_data.columns if col != 'Line Item']
        
        # Find the row indices for key metrics
        revenue_row = pl_data[pl_data['Line Item'] == 'Revenue'].index
        etsy_fees_row = pl_data[pl_data['Line Item'] == 'Etsy Fees'].index
        refund_row = pl_data[pl_data['Line Item'] == 'Refund Cost'].index
        
        total_revenue = 0
        total_etsy_fees = 0
        total_refund_cost = 0
        
        if not revenue_row.empty:
            if 'Full Year' in numeric_columns:
                total_revenue = pl_data.loc[revenue_row[0], 'Full Year']
            else:
                total_revenue = pl_data.loc[revenue_row[0], numeric_columns].sum()
        if not etsy_fees_row.empty:
            if 'Full Year' in numeric_columns:
                total_etsy_fees = pl_data.loc[etsy_fees_row[0], 'Full Year']
            else:
                total_etsy_fees = pl_data.loc[etsy_fees_row[0], numeric_columns].sum()
        if not refund_row.empty:
            if 'Full Year' in numeric_columns:
                total_refund_cost = pl_data.loc[refund_row[0], 'Full Year']
            else:
                total_refund_cost = pl_data.loc[refund_row[0], numeric_columns].sum()
        
        # Display key metrics (totals across all months)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Total Revenue",
                value=f"${total_revenue:,.2f}",
                help="Total revenue from sales across all months"
            )
        
        with col2:
            st.metric(
                label="💳 Total Etsy Fees",
                value=f"${total_etsy_fees:,.2f}",
                help="Total fees paid to Etsy across all months"
            )
        
        with col3:
            st.metric(
                label="🔄 Total Refund Cost",
                value=f"${total_refund_cost:,.2f}",
                help="Total refunds given to customers"
            )
        
        with col4:
            # Show total costs instead of calculated profit
            total_costs = total_etsy_fees + total_refund_cost
            st.metric(
                label="💸 Total Costs",
                value=f"${total_costs:,.2f}",
                help="Total costs (Etsy Fees + Refunds) across all months"
            )
    else:
        st.info("No Profit & Loss data available for the selected period")
    
    # Render description for profit & loss summary table
    render_profit_loss_summary_table_description(start_date_str, end_date_str)
    
    st.markdown("---")
    
    # =============================================================================
    # PROFIT & LOSS LINE CHART SECTION
    # =============================================================================
    
    # Profit & Loss Line Chart
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📈 Profit & Loss Trends")
    with col2:
        if st.button("📋 Show Description", key="btn_pl_line_chart_description", width='stretch'):
            st.session_state.show_profit_loss_line_chart_description = not st.session_state.get('show_profit_loss_line_chart_description', False)
            st.rerun()

    # Use the same dashboard-level date filters and view mode as the table
    with st.spinner("Loading Profit & Loss line chart data..."):
        if view_mode == 'Year':
            chart_view_mode_param = 'year'
        elif view_mode == 'Month/Year':
            chart_view_mode_param = 'month_year'
        else:
            chart_view_mode_param = 'month'
        pl_chart_data = get_profit_loss_line_chart_data(start_date_str, end_date_str, view_mode=chart_view_mode_param)

    if not pl_chart_data.empty:
        # Get unique line items for selection
        available_line_items = pl_chart_data['Line Item'].unique().tolist()
        
        # Always add "Profit" to available options since it's calculated dynamically
        if 'Profit' not in available_line_items:
            available_line_items.append('Profit')
        
        # Initialize session state for selected line items
        if 'pl_line_chart_selected_items' not in st.session_state:
            st.session_state.pl_line_chart_selected_items = ['Revenue']
        
        # Filter session state to only include valid options
        valid_session_items = [item for item in st.session_state.pl_line_chart_selected_items if item in available_line_items]
        if not valid_session_items:
            valid_session_items = ['Revenue']
        st.session_state.pl_line_chart_selected_items = valid_session_items
        
        # Line item selection
        st.markdown("**Select line items to display:**")
        selected_line_items = st.multiselect(
            "Line Items:",
            options=available_line_items,
            default=valid_session_items,
            key="pl_line_items_selector"
        )
        
        # Update session state
        st.session_state.pl_line_chart_selected_items = selected_line_items
        
        if selected_line_items:
            # Calculate Profit values using the same formula as the table
            if 'Profit' in selected_line_items and st.session_state.get('profit_formula_items', []):
                # Create profit data based on selected formula items
                profit_data = []
                for _, period_row in pl_chart_data.iterrows():
                    if period_row['Line Item'] == 'Revenue':  # Use any line item to get periods
                        period = period_row['Period']
                        
                        # Calculate profit for this period using the formula
                        profit_value = 0
                        for item in st.session_state.profit_formula_items:
                            item_data = pl_chart_data[
                                (pl_chart_data['Line Item'] == item) & 
                                (pl_chart_data['Period'] == period)
                            ]
                            if not item_data.empty:
                                item_value = item_data['Amount (USD)'].iloc[0]
                                if item == 'Revenue':
                                    profit_value += item_value
                                else:
                                    profit_value -= item_value
                        
                        profit_data.append({
                            'Period': period,
                            'Line Item': 'Profit',
                            'Amount (USD)': profit_value
                        })
                
                # Add profit data to chart data
                profit_df = pd.DataFrame(profit_data)
                pl_chart_data = pd.concat([pl_chart_data, profit_df], ignore_index=True)
            
            # Filter data for selected line items
            filtered_chart_data = pl_chart_data[pl_chart_data['Line Item'].isin(selected_line_items)]
            
            # Create line chart
            fig = px.line(
                filtered_chart_data,
                x='Period',
                y='Amount (USD)',
                color='Line Item',
                title="Profit & Loss Trends Over Time",
                labels={'Amount (USD)': 'Amount (USD)', 'Period': 'Period'},
                markers=True
            )
            
            fig.update_layout(
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                title_font_color='white',
                xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)'),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
            
            fig.update_traces(line=dict(width=3), marker=dict(size=6))
            st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
            
        else:
            st.info("Please select at least one line item to display the chart")
    else:
        st.info("No Profit & Loss line chart data available for the selected period")
    
    # Render description for profit & loss line chart
    if st.session_state.get('show_profit_loss_line_chart_description', False):
        with st.expander("📋 Profit & Loss Line Chart Description", expanded=True):
            st.markdown(textwrap.dedent("""
            **PROFIT & LOSS LINE CHART (TRENDS OVER TIME)**

            **Purpose:** Shows trends of different line items over time periods

            **Data Source:** All calculations from fact_financial_transactions table

            **Features:**
            - Interactive line chart with markers
            - Multiple line items can be selected for comparison
            - Profit line is calculated dynamically based on selected formula
            - Time periods match the selected view mode (Month/Year/Month-Year)

            **Line Items Available:**
            - Revenue, Refund Cost, Etsy Fees, VAT, Cost of Goods, Profit
            - Profit is calculated using the same formula as the summary table
            - Users can select/deselect line items to focus on specific metrics

            **View Modes:**
            - **Month**: Shows trends by month across all years
            - **Year**: Shows trends by year
            - **Month/Year**: Shows trends by month and year combination
            """))
            
            # Close button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_profit_loss_line_chart_description_btn", width='stretch'):
                    st.session_state.show_profit_loss_line_chart_description = False
                    st.rerun()
    
    st.markdown("---")
    
    # =============================================================================
    # REVENUE EXPENSES PROFIT STACKED BAR CHART SECTION
    # =============================================================================
    
    # Revenue, Expenses, Profit Stacked Bar Chart
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📊 Revenue vs Operating Expenses vs Profit")
    with col2:
        if st.button("📋 Show Description", key="btn_revenue_expenses_profit_description", width='stretch'):
            st.session_state.show_revenue_expenses_profit_description = not st.session_state.get('show_revenue_expenses_profit_description', False)
            st.rerun()

    # Use the same dashboard-level date filters and view mode as the table
    with st.spinner("Loading Revenue, Expenses, and Profit data..."):
        if view_mode == 'Year':
            bar_view_mode_param = 'year'
        elif view_mode == 'Month/Year':
            bar_view_mode_param = 'month_year'
        else:
            bar_view_mode_param = 'month'
        bar_chart_data = get_revenue_expenses_profit_bar_data(start_date_str, end_date_str, view_mode=bar_view_mode_param)

    if not bar_chart_data.empty:
        # Calculate Profit values using the same formula as the table
        if st.session_state.get('profit_formula_items', []):
            # Update profit values in bar chart data
            for period in bar_chart_data['Period'].unique():
                period_data = bar_chart_data[bar_chart_data['Period'] == period]
                revenue_row = period_data[period_data['Category'] == 'Revenue']
                
                if not revenue_row.empty:
                    # Calculate profit for this period using the formula
                    profit_value = 0
                    for item in st.session_state.profit_formula_items:
                        # Get the value for this item and period from the line chart data
                        item_data = pl_chart_data[
                            (pl_chart_data['Line Item'] == item) & 
                            (pl_chart_data['Period'] == period)
                        ]
                        if not item_data.empty:
                            item_value = item_data['Amount (USD)'].iloc[0]
                            if item == 'Revenue':
                                profit_value += item_value
                            else:
                                profit_value -= item_value
                    
                    # Update profit value in bar chart data
                    bar_chart_data.loc[
                        (bar_chart_data['Period'] == period) & 
                        (bar_chart_data['Category'] == 'Profit'), 
                        'Amount (USD)'
                    ] = profit_value
        
        # Create stacked bar chart
        fig = px.bar(
            bar_chart_data,
            x='Period',
            y='Amount (USD)',
            color='Category',
            title="Revenue vs Operating Expenses vs Profit (USD)",
            labels={'Amount (USD)': 'Amount (USD)', 'Period': 'Period'},
            color_discrete_map={
                'Revenue': '#4ECDC4',
                'Operating Expenses': '#FF6B6B', 
                'Profit': '#FFA726'
            }
        )
        
        fig.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            title_font_color='white',
            xaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)'),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        st.plotly_chart(fig, config={'displayModeBar': True, 'displaylogo': False})
        
    else:
        st.info("No Revenue, Expenses, and Profit data available for the selected period")
    
    # Render description for revenue expenses profit bar chart
    if st.session_state.get('show_revenue_expenses_profit_description', False):
        with st.expander("📋 Revenue vs Operating Expenses vs Profit Description", expanded=True):
            st.markdown(textwrap.dedent("""
            **REVENUE VS OPERATING EXPENSES VS PROFIT BAR CHART**

            **Purpose:** Shows comparison between Revenue, Operating Expenses, and Profit across different time periods

            **Data Source:** All calculations from fact_financial_transactions table

            **Features:**
            - Stacked bar chart showing three main categories
            - Revenue: Total sales amount
            - Operating Expenses: Sum of Etsy Fees and VAT
            - Profit: Calculated using the same formula as summary table
            - Color-coded bars for easy comparison

            **Color Scheme:**
            - **Revenue**: Teal (#4ECDC4)
            - **Operating Expenses**: Red (#FF6B6B)
            - **Profit**: Orange (#FFA726)

            **View Modes:**
            - **Month**: Shows data by month across all years
            - **Year**: Shows data by year
            - **Month/Year**: Shows data by month and year combination

            **Calculation:**
            - Revenue = Amount with Type = Sale
            - Operating Expenses = Etsy Fees + VAT
            - Profit = Revenue - (selected expenses based on formula)
            """))
            
            # Close button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("❌ Close", key="close_revenue_expenses_profit_description_btn", width='stretch'):
                    st.session_state.show_revenue_expenses_profit_description = False
                    st.rerun()
