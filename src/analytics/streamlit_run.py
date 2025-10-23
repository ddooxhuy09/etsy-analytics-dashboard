import streamlit as st
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import dashboard modules
from src.analytics.dashboard.streamlit_dashboard import render_dashboard
from src.analytics.reports.streamlit_account_statement import render_account_statement
from src.analytics.dashboard.profit_loss_statement.profit_loss_statement import render_profit_loss_statement

def main():
    """Main Streamlit application with tabs"""
    
    # Page config
    st.set_page_config(
        page_title="Etsy Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("📊 Etsy Analytics Dashboard")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "📋 Account Statement", "💰 Profit & Loss"])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_account_statement()
    
    with tab3:
        render_profit_loss_statement()

if __name__ == "__main__":
    main()
