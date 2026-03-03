import streamlit as st
import pandas as pd
from modules.calculations import calculate_client_metrics
from ui.notes_view import render_notes_section
from ui.tasks_view import render_tasks_section
from ui.documents_view import render_documents_section
from ui.can_management import render_can_management

def render_task_table(db, tasks_df, key_prefix):
    """Renders a tasks table with interactive status dropdowns."""
    if tasks_df.empty:
        return
    
    # Ensure correct column names for display
    display_df = tasks_df.copy()
    if 'client_name' not in display_df.columns and 'owner_name' in display_df.columns:
        display_df['client_name'] = display_df['owner_name']
    
    # Selection of columns
    cols = ['id', 'client_name', 'description', 'due_date', 'status', 'priority']
    available_cols = [c for c in cols if c in display_df.columns]
    
    edited_df = st.data_editor(
        display_df[available_cols],
        column_config={
            "id": None, # Hide ID
            "status": st.column_config.SelectboxColumn(
                "Status",
                help="Update task status",
                options=["Pending", "In Progress", "Completed", "Cancelled"],
                required=True,
            ),
            "client_name": st.column_config.TextColumn("Client", disabled=True),
            "description": st.column_config.TextColumn("Task", disabled=True),
            "due_date": st.column_config.DateColumn("Due Date", disabled=True),
            "priority": st.column_config.TextColumn("Priority", disabled=True)
        },
        hide_index=True,
        key=f"{key_prefix}_editor",
        use_container_width=True
    )
    
    # Handle changes via session state if necessary, but st.data_editor with keys is tricky.
    # Better approach: check the state of the editor.
    if f"{key_prefix}_editor" in st.session_state:
        edits = st.session_state[f"{key_prefix}_editor"].get("edited_rows", {})
        if edits:
            for idx_str, changes in edits.items():
                if "status" in changes:
                    idx = int(idx_str)
                    task_id = int(display_df.iloc[idx]['id'])
                    new_status = changes["status"]
                    db.update_task_status(task_id, new_status)
                    # Sync with tasks_view.py session state if it exists to ensure cross-tab consistency
                    st.session_state[f"task_{task_id}"] = new_status
            st.rerun()

def render_dashboard(db):
    st.title("Distributor Dashboard")
    
    # Pre-fetch global data
    clients_df = db.get_all_clients()
    total_clients = len(clients_df)
    metrics_summary = db.get_total_metrics()
    total_aum = metrics_summary['total_aum']
    
    tab_overview, tab_clients = st.tabs(["📊 Distributor Overview", "👤 Client Overview"])
    
    with tab_overview:
        # 1. High-level Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # Overdue Tasks Check
        overdue_tasks = db.get_overdue_tasks()
        num_overdue = len(overdue_tasks)

        col1.metric("Total AUM", f"₹{total_aum:,.2f}")
        col2.metric("Active Clients", str(total_clients))
        col3.metric("SIP Book (Monthly)", "₹0.00")
        col4.metric("Overdue Tasks", str(num_overdue), delta=f"-{num_overdue}" if num_overdue > 0 else None, delta_color="inverse")
        
        st.divider()
        
        # 2. Global Tasks View
        st.subheader("📋 Tasks Overview")
        t_col1, t_col2 = st.columns(2)
        
        with t_col1:
            st.write("### ⚠️ Overdue Tasks")
            if not overdue_tasks.empty:
                render_task_table(db, overdue_tasks, "overdue")
            else:
                st.success("No overdue tasks!")
                
        with t_col2:
            st.write("### 🕒 Current Tasks")
            all_tasks = db.get_tasks()
            if not all_tasks.empty:
                current_tasks = all_tasks[all_tasks['status'].isin(['Pending', 'In Progress'])]
                if not current_tasks.empty:
                    render_task_table(db, current_tasks, "current")
                else:
                    st.info("No active tasks.")
            else:
                st.info("No tasks recorded.")

    with tab_clients:
        # 3. Client List & Portfolio Drill-down
        if not clients_df.empty:
            st.subheader("Your Clients")
            # Simplified view for the table
            display_df = clients_df[['client_id', 'name', 'pan', 'kyc_status']]
            st.dataframe(display_df, width='stretch')
            
            selected_client_id = st.selectbox("Select Client to View Profile", 
                                            options=clients_df['client_id'].tolist(),
                                            format_func=lambda x: clients_df[clients_df['client_id'] == x]['name'].iloc[0])
            
            if selected_client_id:
                st.divider()
                c_tab1, c_tab2, c_tab3, c_tab4 = st.tabs(["Portfolio", "Notes", "Tasks", "Documents"])
                
                # Pre-fetch client data for all tabs to use
                client_data = clients_df[clients_df['client_id'] == selected_client_id].iloc[0]

                with c_tab1:
                    k_col1, k_col2 = st.columns([1, 1])
                    with k_col1:
                        st.write(f"**PAN:** {client_data['pan']}")
                        
                        # Fetch CANs for dropdown
                        cans_df = db.get_client_cans(selected_client_id)
                        can_options = [{"label": "ALL Folios", "value": "ALL"}]
                        if not cans_df.empty:
                            for _, can in cans_df.iterrows():
                                desc = f" ({can['can_description']})" if can.get('can_description') else ""
                                can_options.append({"label": f"{can['can_number']}{desc}", "value": can['id']})
                        
                        can_options.append({"label": "---", "value": "SEPARATOR"})
                        can_options.append({"label": "➕ Add New CAN", "value": "ADD_NEW"})
                        can_options.append({"label": "⚙️ Manage CANs", "value": "MANAGE"})
                                
                        selected_can = st.selectbox(
                            "CAN Selection / Management",
                            options=can_options,
                            format_func=lambda x: x["label"],
                            key=f"can_filter_{selected_client_id}",
                            disabled=False
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
                    
                    # Conditional Rendering based on CAN selection
                    if selected_can_id == "ADD_NEW":
                        render_can_management(db, selected_client_id, show_add=True, show_list=False)
                    elif selected_can_id == "MANAGE":
                        render_can_management(db, selected_client_id, show_add=False, show_list=True)
                    elif selected_can_id == "SEPARATOR":
                        st.warning("Please select a valid option.")
                    else:
                        # Metrics now calculated based on selected CAN
                        actual_can_id = None if selected_can_id == "ALL" else selected_can_id
                        calc_df = db.get_transactions_for_calculations(selected_client_id, can_id=actual_can_id)
                        metrics = calculate_client_metrics(calc_df)
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric(f"{'Filtered' if actual_can_id else 'Client'} AUM", f"₹{metrics['aum']:,.2f}")
                        c2.metric("Net Investment", f"₹{metrics['net_investment']:,.2f}")
                        c3.metric("Total Gain", f"₹{metrics['total_gain']:,.2f}")
                        c4.metric("XIRR", f"{metrics['xirr']:.2%}")
                        
                        st.write("### Portfolio Details")
                        portfolio_df = db.get_client_portfolio(selected_client_id, can_id=actual_can_id)
                        if not portfolio_df.empty:
                            st.table(portfolio_df)
                        else:
                            st.info("No transactions found for this client/CAN.")

                with c_tab2:
                    render_notes_section(db, client_id=selected_client_id)
                    
                with c_tab3:
                    render_tasks_section(db, client_id=selected_client_id)
                    
                with c_tab4:
                    render_documents_section(db, selected_client_id)

        else:
            st.info("No clients onboarded yet. Go to 'Client Management' to add your first client.")
