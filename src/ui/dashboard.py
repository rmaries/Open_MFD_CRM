import streamlit as st
import pandas as pd
from modules.calculations import calculate_client_metrics
from ui.notes_view import render_notes_section
from ui.tasks_view import render_tasks_section
from ui.documents_view import render_documents_section
from ui.can_management import render_can_management

def render_dashboard(db):
    st.title("Distributor Dashboard")
    
    # 1. High-level Metrics
    clients_df = db.get_all_clients()
    total_clients = len(clients_df)
    
    metrics_summary = db.get_total_metrics()
    total_aum = metrics_summary['total_aum']
    
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
            tab1, tab2, tab3, tab4 = st.tabs(["Portfolio", "Notes", "Tasks", "Documents"])
            
            # Pre-fetch client data for all tabs to use
            client_data = clients_df[clients_df['client_id'] == selected_client_id].iloc[0]

            with tab1:
                k_col1, k_col2 = st.columns([1, 1])
                with k_col1:
                    st.write(f"**PAN:** {client_data['pan']}")
                    
                    # Fetch CANs for dropdown
                    cans_df = db.get_client_cans(selected_client_id)
                    can_options = [{"label": "ALL", "value": None}]
                    if not cans_df.empty:
                        for _, can in cans_df.iterrows():
                            desc = f" ({can['can_description']})" if can.get('can_description') else ""
                            can_options.append({"label": f"{can['can_number']}{desc}", "value": can['id']})
                            
                    selected_can = st.selectbox(
                        "Filter Portfolio by CAN",
                        options=can_options,
                        format_func=lambda x: x["label"],
                        key=f"can_filter_{selected_client_id}"
                    )
                    selected_can_id = selected_can["value"]

                with k_col2:
                    kyc_status = st.toggle("KYC Verified", value=bool(client_data['kyc_status']), key=f"kyc_{selected_client_id}")
                    if kyc_status != bool(client_data['kyc_status']):
                        db.update_client_kyc(selected_client_id, kyc_status)
                        st.success("KYC status updated!")
                        st.rerun()
                    st.write(f"**Email:** {client_data.get('email', 'N/A')}")
                    st.write(f"**Phone:** {client_data.get('phone', 'N/A')}")

                
                # Edit Profile Section
                with st.expander("📝 Edit Client Profile"):
                    with st.form(f"edit_profile_{selected_client_id}"):
                        new_name = st.text_input("Name", value=client_data['name'])
                        new_pan = st.text_input("PAN", value=client_data['pan'] if client_data['pan'] else "")
                        new_email = st.text_input("Email", value=client_data['email'] if client_data['email'] else "")
                        new_phone = st.text_input("Phone", value=client_data['phone'] if client_data['phone'] else "")
                        new_can = st.text_input("MFU CAN", value=client_data['can_number'] if client_data['can_number'] else "")
                        
                        if st.form_submit_button("Update Profile"):
                            if not new_name or not new_phone:
                                st.error("Name and Phone are required!")
                            else:
                                try:
                                    db.update_client_info(
                                        selected_client_id,
                                        name=new_name,
                                        pan=new_pan if new_pan else None,
                                        email=new_email if new_email else None,
                                        phone=new_phone,
                                        can_number=new_can if new_can else None
                                    )
                                    st.success("Profile updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating profile: {e}")

                st.divider()
                
                st.divider()
                
                # Metrics now calculated based on selected CAN
                calc_df = db.get_transactions_for_calculations(selected_client_id, can_id=selected_can_id)
                metrics = calculate_client_metrics(calc_df)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(f"{'Filtered' if selected_can_id else 'Client'} AUM", f"₹{metrics['aum']:,.2f}")
                c2.metric("Net Investment", f"₹{metrics['net_investment']:,.2f}")
                c3.metric("Total Gain", f"₹{metrics['total_gain']:,.2f}")
                c4.metric("XIRR", f"{metrics['xirr']:.2%}")
                
                st.write("### Portfolio Details")
                portfolio_df = db.get_client_portfolio(selected_client_id, can_id=selected_can_id)
                if not portfolio_df.empty:
                    st.table(portfolio_df)
                else:
                    st.info("No transactions found for this client/CAN.")
                    
                st.divider()
                with st.expander("⚙️ Manage CAN Numbers"):
                    render_can_management(db, selected_client_id)

            
            with tab2:
                render_notes_section(db, client_id=selected_client_id)
                
            with tab3:
                render_tasks_section(db, client_id=selected_client_id)
                
            with tab4:
                render_documents_section(db, selected_client_id)

    else:
        st.info("No clients onboarded yet. Go to 'Client Management' to add your first client.")
