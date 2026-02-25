import streamlit as st
import pandas as pd
from modules.calculations import calculate_client_metrics
from ui.components import render_notes_section, render_tasks_section

def render_dashboard(db):
    st.title("Distributor Dashboard")
    
    # 1. High-level Metrics
    clients_df = db.get_all_clients()
    total_clients = len(clients_df)
    
    total_aum = 0.0
    for _, client in clients_df.iterrows():
        metrics = calculate_client_metrics(client['client_id'], db)
        total_aum += metrics['aum']
    
    # Overdue Tasks Check
    overdue_tasks = db.get_overdue_tasks()
    num_overdue = len(overdue_tasks)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total AUM", f"₹{total_aum:,.2f}")
    col2.metric("Active Clients", str(total_clients))
    col3.metric("SIP Book (Monthly)", "₹0.00")
    col4.metric("Overdue Tasks", str(num_overdue), delta=f"-{num_overdue}" if num_overdue > 0 else None, delta_color="inverse")
    
    if num_overdue > 0:
        with st.expander("⚠️ View Overdue Tasks", expanded=False):
            st.table(overdue_tasks[['client_name', 'description', 'due_date', 'priority']])

    st.divider()
    
    # 2. Client List & Portfolio Drill-down
    st.subheader("Your Clients")
    if not clients_df.empty:
        # Simplified view for the table
        display_df = clients_df[['client_id', 'name', 'pan', 'kyc_status']]
        st.dataframe(display_df, width='stretch')
        
        selected_client_id = st.selectbox("Select Client to View Profile", 
                                        options=clients_df['client_id'].tolist(),
                                        format_func=lambda x: clients_df[clients_df['client_id'] == x]['name'].iloc[0])
        
        if selected_client_id:
            tab1, tab2, tab3 = st.tabs(["Portfolio", "Notes", "Tasks"])
            
            with tab1:
                metrics = calculate_client_metrics(selected_client_id, db)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Client AUM", f"₹{metrics['aum']:,.2f}")
                c2.metric("Net Investment", f"₹{metrics['net_investment']:,.2f}")
                c3.metric("Total Gain", f"₹{metrics['total_gain']:,.2f}")
                c4.metric("XIRR", f"{metrics['xirr']:.2%}")
                
                st.write("### Portfolio Details")
                portfolio_df = db.get_client_portfolio(selected_client_id)
                if not portfolio_df.empty:
                    st.table(portfolio_df)
                else:
                    st.info("No transactions found for this client.")
            
            with tab2:
                render_notes_section(db, selected_client_id)
                
            with tab3:
                render_tasks_section(db, selected_client_id)
    else:
        st.info("No clients onboarded yet. Go to 'Client Management' to add your first client.")
