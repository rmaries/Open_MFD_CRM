import streamlit as st
import pandas as pd
from modules.database import Database
from ui.dashboard import render_dashboard
from ui.client_form import input_client_details
from ui.transaction_form import transaction_entry
import shutil
import os
from datetime import datetime


def main():
    st.set_page_config(page_title="Open-MFD CRM", layout="wide")
    
    # 1. Database Initialization
    db = Database()

    # Custom CSS for Navbar
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {display: none;}
        .nav-button {
            width: 100%;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 5px;
            border: none;
            background: none;
            text-align: left;
            cursor: pointer;
            transition: 0.3s;
        }
        .nav-button:hover {
            background-color: #f0f2f6;
        }
        .active-nav {
            background-color: #e6f0ff;
            color: #0066cc;
            font-weight: bold;
            border-left: 5px solid #0066cc;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state for navigation
    if "choice" not in st.session_state:
        st.session_state.choice = "Dashboard"

    # Sidebar Navigation
    with st.sidebar:
        st.title("🚀 Open-MFD")
        st.caption("v1.0.0 | CRM for MFDs")
        st.divider()
        
        menu_items = {
            "Dashboard": "🏠",
            "Client Management": "👤",
            "Investment Tracking": "📈",
            "MFU Integration": "🔗",
            "User Guide": "📖",
            "Settings": "⚙️"
        }
        
        for item, icon in menu_items.items():
            if st.button(f"{icon} {item}", use_container_width=True, 
                         type="primary" if st.session_state.choice == item else "secondary"):
                st.session_state.choice = item
                st.rerun()

    choice = st.session_state.choice
    
    if choice == "Dashboard":
        render_dashboard(db)
    elif choice == "Client Management":
        input_client_details(db)
    elif choice == "Investment Tracking":
        transaction_entry(db)
    elif choice == "MFU Integration":
        st.header("🔗 MFU Integration")
        st.info("MFU API Connection logic will be implemented here.")
    elif choice == "User Guide":
        guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "USER_GUIDE.md")
        if os.path.exists(guide_path):
            with open(guide_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.error("User Guide not found.")
    elif choice == "Settings":
        st.header("⚙️ Settings")
        st.write("Database Path:", db.db_path)
        
        st.divider()
        st.subheader("Data Maintenance")
        st.warning("Critical actions below. Please use with caution.")
        
        confirm_reset = st.checkbox("I understand that resetting the database is irreversible.")
        
        if st.button("Reset Database (Demo Mode)", disabled=not confirm_reset):
            # 1. Create a backup first just in case
            if os.path.exists(db.db_path):
                backup_dir = "data/backups"
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
                shutil.copy2(db.db_path, backup_path)
                st.info(f"Backup created at {backup_path}")
            
            # 2. Perform reset
            if os.path.exists(db.db_path):
                os.remove(db.db_path)
                st.success("Database reset. Please refresh the page.")
            else:
                st.error("Database file not found.")

if __name__ == "__main__":
    main()
