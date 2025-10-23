"""
Streamlit Account Statement Report - For Tab Integration
"""
import streamlit as st
import pandas as pd
import psycopg2
import os
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import base64
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.analytics.utils.postgres_connection import execute_query_with_cache

# Database configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'etsy'),
    'user': os.getenv('POSTGRES_USER', 'etsy'),
    'password': os.getenv('POSTGRES_PASSWORD', 'etsy')
}

def execute_query(query: str, params: tuple = None) -> pd.DataFrame:
    """Execute SQL query and return DataFrame"""
    return execute_query_with_cache(query, params, ttl=300)

def get_bank_account_table_data() -> pd.DataFrame:
    """Get Bank Account Table data"""
    sql = """WITH bank_account_stats AS (
                SELECT 
                    fbt.bank_account_key,
                    COUNT(*) as transaction_count,
                    SUM(COALESCE(fbt.credit_amount, 0)) as total_credit,
                    SUM(COALESCE(fbt.debit_amount, 0)) as total_debit,
                    MIN(dt.full_date) as first_transaction_date,
                    MAX(dt.full_date) as last_transaction_date,
                    MAX(fbt.balance_after_transaction) as current_balance
                FROM fact_bank_transactions fbt
                JOIN dim_time dt ON fbt.transaction_date_key = dt.time_key
                GROUP BY fbt.bank_account_key
            )
            SELECT 
                dba.account_number as "Account Number",
                dba.account_name as "Account Name",
                dba.cif_number as "CIF Number",
                dba.customer_address as "Customer Address",
                dba.opening_date as "Opening Date",
                dba.currency_code as "Currency",
                bas.transaction_count as "Total Transactions",
                ROUND(bas.total_credit, 2) as "Total Credit (VND)",
                ROUND(bas.total_debit, 2) as "Total Debit (VND)",
                ROUND(bas.current_balance, 2) as "Current Balance (VND)",
                bas.first_transaction_date as "First Transaction Date",
                bas.last_transaction_date as "Last Transaction Date"
            FROM bank_account_stats bas
            JOIN dim_bank_account dba ON bas.bank_account_key = dba.bank_account_key
            WHERE dba.account_number IS NOT NULL AND dba.account_number <> ''
            ORDER BY bas.total_credit DESC
            LIMIT 1000"""
    
    return execute_query(sql)

def get_bank_account_info(account_number: str) -> dict:
    """Get bank account information for account statement"""
    sql = """
    SELECT 
        dba.account_number,
        dba.account_name,
        dba.cif_number,
        dba.customer_address,
        dba.opening_date,
        dba.currency_code
    FROM dim_bank_account dba
    WHERE dba.account_number = %s
    """
    
    df = execute_query(sql, (account_number,))
    
    if not df.empty:
        row = df.iloc[0]
        
        return {
            'account_name': row['account_name'] if pd.notna(row['account_name']) else 'N/A',
            'account_number': row['account_number'] if pd.notna(row['account_number']) else 'N/A',
            'cif_number': row['cif_number'] if pd.notna(row['cif_number']) else 'N/A',
            'customer_address': row['customer_address'] if pd.notna(row['customer_address']) else 'N/A',
            'opening_date': row['opening_date'] if pd.notna(row['opening_date']) else 'N/A',
            'currency_code': row['currency_code'] if pd.notna(row['currency_code']) else 'VND'
        }
    
    return {
        'account_name': 'N/A', 
        'account_number': 'N/A', 
        'cif_number': 'N/A',
        'customer_address': 'N/A',
        'opening_date': 'N/A',
        'currency_code': 'VND'
    }

def get_account_statement_data(account_number: str, from_date: str = None, to_date: str = None) -> pd.DataFrame:
    """Get account statement data for specific bank account"""
    sql = """
    SELECT 
        t.full_date AS "Ngày GD",
        fbt.reference_number AS "Mã giao dịch",
        dba.account_number AS "Số tài khoản truy vấn",
        dba.account_name AS "Tên tài khoản truy vấn",
        dba.opening_date AS "Ngày mở tài khoản",
        COALESCE(fbt.credit_amount, 0) AS "Phát sinh có",
        COALESCE(fbt.debit_amount, 0) AS "Phát sinh nợ",
        fbt.balance_after_transaction AS "Số dư",
        fbt.transaction_description AS "Diễn giải"
    FROM fact_bank_transactions fbt
    JOIN dim_time t ON fbt.transaction_date_key = t.time_key
    JOIN dim_bank_account dba ON fbt.bank_account_key = dba.bank_account_key
    WHERE dba.account_number = %s
    """
    
    params = [account_number]
    
    if from_date:
        sql += " AND t.full_date >= %s"
        params.append(from_date)
    
    if to_date:
        sql += " AND t.full_date <= %s"
        params.append(to_date)
    
    sql += " ORDER BY t.full_date, fbt.bank_transaction_key"
    
    return execute_query(sql, tuple(params))

def create_pdf_report(account_info: dict, account_data: pd.DataFrame, from_date: str = None, to_date: str = None) -> bytes:
    """Create PDF report for Account Statement"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)

    # Register Times New Roman font
    try:
        # Try to register Times New Roman (common on Windows)
        pdfmetrics.registerFont(TTFont('Times-Roman', 'times.ttf'))
        pdfmetrics.registerFont(TTFont('Times-Bold', 'timesbd.ttf'))
        font_name = 'Times-Roman'
        font_bold = 'Times-Bold'
    except:
        # Fallback to default fonts
        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=16,
        spaceAfter=20,
        alignment=1  # Center alignment
    )

    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=14,
        spaceAfter=6
    )

    # Build content
    story = []

    # Title
    story.append(Paragraph("SAO KÊ TÀI KHOẢN/ ACCOUNT STATEMENT", title_style))
    story.append(Spacer(1, 10))

    # Time generated - centered
    current_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    time_style = ParagraphStyle(
        'TimeGenerated',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=14,
        spaceAfter=10,
        alignment=1  # Center alignment
    )
    story.append(Paragraph(f"Thời gian xuất/ Time generated: {current_time}", time_style))
    story.append(Spacer(1, 10))

    # Date range - centered and on same line
    date_range_style = ParagraphStyle(
        'DateRange',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=14,
        spaceAfter=15,
        alignment=1  # Center alignment
    )
    from_date_str = from_date or 'All time'
    to_date_str = to_date or 'Present'
    story.append(Paragraph(f"Từ ngày/ From: {from_date_str} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Đến ngày/ To: {to_date_str}", date_range_style))
    story.append(Spacer(1, 15))

    # Bank Account Information - Paired format with right alignment
    # Create a table for better alignment control
    account_info_data = [
        [
            f"Số tài khoản/ Account Number: {account_info['account_number']}", 
            f"Loại tiền/ Currency: {account_info['currency_code']}"
        ],
        [
            f"Tên tài khoản/ Account Name: {account_info['account_name']}", 
            f"CIF Number: {account_info['cif_number']}"
        ],
        [
            f"Địa chỉ/ Address: {account_info['customer_address']}", 
            ""
        ]
    ]
    
    account_info_table = Table(account_info_data, colWidths=[4*inch, 4*inch])
    account_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Left column - left aligned
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # Right column - right aligned
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(account_info_table)
    story.append(Spacer(1, 15))

    # Transaction Details
    if not account_data.empty:
        # Prepare transaction data for table
        transaction_data = [['Ngày GD\n(Transaction Date)', 'Mã giao dịch\n(Reference No.)', 'Số tài khoản truy vấn\n(Account Number)', 'Tên tài khoản truy vấn\n(Account Name)', 'Ngày mở tài khoản\n(Opening Date)', 'Phát sinh có\n(Credit Amount)', 'Phát sinh nợ\n(Debit Amount)', 'Số dư\n(Balance)', 'Diễn giải\n(Description)']]

        for _, row in account_data.iterrows():
            # Format amounts based on currency (VND doesn't use $ symbol)
            currency_symbol = "₫" if account_info.get('currency_code', 'VND') == 'VND' else "$"
            transaction_data.append([
                str(row['Ngày GD']),
                str(row['Mã giao dịch']),
                str(row['Số tài khoản truy vấn']),
                str(row['Tên tài khoản truy vấn']),
                str(row['Ngày mở tài khoản']),
                f"{currency_symbol}{row['Phát sinh có']:,.0f}" if row['Phát sinh có'] > 0 else "",
                f"{currency_symbol}{row['Phát sinh nợ']:,.0f}" if row['Phát sinh nợ'] > 0 else "",
                f"{currency_symbol}{row['Số dư']:,.0f}",
                str(row['Diễn giải'])[:80] + "..." if len(str(row['Diễn giải'])) > 80 else str(row['Diễn giải'])
            ])

        # Create transaction table - simple style, no background
        transaction_table = Table(transaction_data, colWidths=[1*inch, 1.2*inch, 1*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 2*inch])
        transaction_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(transaction_table)
    else:
        story.append(Paragraph("No transaction data available for the selected period.", normal_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def display_pdf_preview(pdf_data: bytes):
    """Display PDF preview in Streamlit"""
    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def render_bank_account_table():
    """Render bank account table section"""
    st.header("🏦 Bank Account Details")
    
    with st.spinner("Loading bank account data..."):
        bank_account_data = get_bank_account_table_data()
    
    if not bank_account_data.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Accounts", len(bank_account_data))
        
        with col2:
            total_credit = bank_account_data['Total Credit (VND)'].sum()
            st.metric("Total Credit", f"₫{total_credit:,.0f}")
        
        with col3:
            total_debit = bank_account_data['Total Debit (VND)'].sum()
            st.metric("Total Debit", f"₫{total_debit:,.0f}")
        
        with col4:
            total_transactions = bank_account_data['Total Transactions'].sum()
            st.metric("Total Transactions", f"{total_transactions:,}")
        
        # Bank account table
        st.subheader("📋 Bank Account Table")
        
        # Display table with selection
        selected_rows = st.dataframe(
            bank_account_data,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Handle row selection
        if selected_rows.selection.rows:
            selected_row = selected_rows.selection.rows[0]
            selected_account = bank_account_data.iloc[selected_row]["Account Number"]
            st.session_state.selected_account = selected_account
            st.success(f"✅ Selected account: {selected_account}")
        
        # Create Report button
        if 'selected_account' in st.session_state and st.session_state.selected_account:
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            
            with col1:
                create_report = st.button("📋 Create Report", type="primary", use_container_width=True, key="create_report_btn")
            
            with col2:
                st.info(f"Selected: **{st.session_state.selected_account}**")
            
            if create_report:
                st.session_state.show_report = True
                st.rerun()
        
        # Download button
        st.markdown("---")
        csv = bank_account_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Bank Account Table CSV",
            data=csv,
            file_name=f"bank_accounts_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    else:
        st.warning("🏦 No bank account data available")
        st.info("💡 Make sure PostgreSQL is running and has bank data loaded")

def render_account_statement_report():
    """Render account statement report section"""
    if not st.session_state.get('show_report', False) or 'selected_account' not in st.session_state:
        return
    
    st.markdown("---")
    st.header("📋 SAO KÊ TÀI KHOẢN/ ACCOUNT STATEMENT")
    
    selected_account = st.session_state.selected_account
    
    # Bank account info
    st.subheader(f"🏦 Tài khoản: {selected_account}")
    
    # Bank account info section
    account_info = get_bank_account_info(selected_account)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Số tài khoản/ Account Number:** {account_info['account_number']}")
        st.write(f"**Tên tài khoản/ Account Name:** {account_info['account_name']}")
    
    with col2:
        st.write(f"**CIF Number:** {account_info['cif_number']}")
        st.write(f"**Loại tiền/ Currency:** {account_info['currency_code']}")
    
    st.write(f"**Ngày mở tài khoản/ Opening Date:** {account_info['opening_date']}")
    st.write(f"**Địa chỉ/ Address:** {account_info['customer_address']}")
    
    # Close report button
    if st.button("❌ Close Report", key="close_report_btn"):
        st.session_state.show_report = False
        st.rerun()
    
    # Date filters
    st.subheader("📅 Bộ lọc ngày")
    col1, col2 = st.columns(2)
    
    with col1:
        from_date = st.date_input(
            "Từ ngày/ From:",
            value=None,
            key="from_date"
        )
    
    with col2:
        to_date = st.date_input(
            "Đến ngày/ To:",
            value=None,
            key="to_date"
        )
    
    # Get account statement data
    with st.spinner("Loading account statement..."):
        from_date_str = from_date.strftime('%Y-%m-%d') if from_date else None
        to_date_str = to_date.strftime('%Y-%m-%d') if to_date else None
        account_data = get_account_statement_data(selected_account, from_date_str, to_date_str)
    
    if not account_data.empty:
        # Account statement table
        st.subheader("📋 Chi tiết giao dịch")
        
        # Display table
        st.dataframe(
            account_data,
            use_container_width=True,
            hide_index=True
        )
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            csv = account_data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"account_statement_{selected_account}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if st.button("📄 Generate PDF Report", key="generate_pdf_btn"):
                with st.spinner("Generating PDF report..."):
                    pdf_data = create_pdf_report(
                        account_info, 
                        account_data, 
                        from_date_str, 
                        to_date_str
                    )
                    
                    # Store PDF data in session state for preview
                    st.session_state.pdf_data = pdf_data
                    st.session_state.show_pdf_preview = True
                    st.rerun()
        
        # PDF Preview and Download
        if st.session_state.get('show_pdf_preview', False) and 'pdf_data' in st.session_state:
            st.markdown("---")
            st.subheader("📄 PDF Preview")
            
            # Display PDF preview
            display_pdf_preview(st.session_state.pdf_data)
            
            # Download button
            st.download_button(
                label="📥 Download PDF",
                data=st.session_state.pdf_data,
                file_name=f"account_statement_{selected_account}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
            
            # Close preview button
            if st.button("❌ Close PDF Preview", key="close_pdf_preview_btn"):
                st.session_state.show_pdf_preview = False
                st.rerun()
        
    else:
        st.warning(f"📊 No transaction data found for account: {selected_account}")
        st.info("💡 This bank account may not have any transactions")

def render_account_statement():
    """Render account statement tab content"""
    
    # Header
    st.header("📋 Account Statement Report")
    st.markdown("---")
    
    # Sidebar for controls
    st.sidebar.header("🔧 Controls")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", type="primary", key="account_refresh"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content
    render_bank_account_table()
    render_account_statement_report()

def main():
    """Main function for standalone execution"""
    st.set_page_config(
        page_title="Account Statement Report",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_account_statement()

if __name__ == "__main__":
    main()