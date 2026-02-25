import streamlit as st
import pandas as pd
from modules.database import Database
from ui.dashboard import render_dashboard

def main():
    st.set_page_config(page_title="Open-MFD CRM", layout="wide")
    
    st.sidebar.title("Open-MFD CRM")
    menu = ["Dashboard", "Client Management", "Investment Tracking", "MFU Integration", "User Guide", "Settings"]
    choice = st.sidebar.selectbox("Menu", menu)
    
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
        st.header("MFU Integration")
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
        st.header("Settings")
        st.write("Database Path:", db.db_path)
        if st.button("Reset Database (Demo)"):
            import os
            if os.path.exists(db.db_path):
                os.remove(db.db_path)
                st.success("Database reset. Please refresh.")

if __name__ == "__main__":
    main()
