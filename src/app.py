import streamlit as st
import pandas as pd
from modules.database import Database
from ui.dashboard import render_dashboard

def main():
    st.set_page_config(page_title="Open-MFD CRM", layout="wide")
    
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
    db = Database()
    
    if choice == "Dashboard":
        render_dashboard(db)
    elif choice == "Client Management":
        from ui.components import input_client_details
        input_client_details(db)
    elif choice == "Investment Tracking":
        from ui.components import transaction_entry
        transaction_entry(db)
    elif choice == "MFU Integration":
        st.header("🔗 MFU Integration")
        st.info("MFU API Connection logic will be implemented here.")
    elif choice == "User Guide":
        import os
        guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "USER_GUIDE.md")
        if os.path.exists(guide_path):
            with open(guide_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.error("User Guide not found.")
    elif choice == "Settings":
        st.header("⚙️ Settings")
        st.write("Database Path:", db.db_path)
        if st.button("Reset Database (Demo)"):
            import os
            if os.path.exists(db.db_path):
                os.remove(db.db_path)
                st.success("Database reset. Please refresh.")

if __name__ == "__main__":
    main()
