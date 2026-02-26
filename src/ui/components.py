import streamlit as st
import pandas as pd
from datetime import datetime

def input_client_details(db):
    """Form to input client onboarding details."""
    st.subheader("Client Onboarding")
    with st.form("onboarding_form", clear_on_submit=True):
        name = st.text_input("Full Name * (as per records)")
        phone = st.text_input("Phone Number *")
        pan = st.text_input("PAN (Optional)").upper()
        email = st.text_input("Email Address (Optional)")
        can = st.text_input("MFU CAN (Optional)")
        
        st.caption("* Required fields")
        submitted = st.form_submit_button("Onboard Client")
        
        if submitted:
            if not name or not phone:
                st.error("Name and Phone Number are required!")
            else:
                try:
                    # Provide None for empty PAN to allow multiple nulls in UNIQUE column
                    client_id = db.add_client(
                        name, 
                        pan if pan else None, 
                        can_number=can if can else None, 
                        email=email if email else None, 
                        phone=phone
                    )
                    st.success(f"Client {name} onboarded successfully! (ID: {client_id})")
                except Exception as e:
                    if "UNIQUE constraint failed: clients.pan" in str(e):
                        st.error(f"Error: A client with PAN {pan} already exists.")
                    else:
                        st.error(f"Error onboarding client: {e}")

def transaction_entry(db):
    """Form to add investment transactions."""
    st.subheader("Add Transaction")
    
    # Fetch clients for selection
    clients_df = db.get_all_clients()
    if clients_df.empty:
        st.warning("Please onboard a client first.")
        return

    client_options = {row['name']: row['client_id'] for _, row in clients_df.iterrows()}
    selected_client_name = st.selectbox("Select Client", list(client_options.keys()))
    client_id = client_options[selected_client_name]

    # Fetch/Select Folio
    # For now, let's allow adding a new folio or selecting an existing one
    query = "SELECT * FROM folios WHERE client_id = ?"
    folios_df = db.run_query(query, params=(client_id,))
    
    folio_id = None
    if not folios_df.empty:
        folio_options = {f"{row['folio_number']} ({row['amc_name']})": row['folio_id'] for _, row in folios_df.iterrows()}
        folio_choice = st.selectbox("Select Folio", ["Add New Folio"] + list(folio_options.keys()))
        if folio_choice != "Add New Folio":
            folio_id = folio_options[folio_choice]

    if folio_id is None:
        new_folio_num = st.text_input("New Folio Number")
        amc_name = st.text_input("AMC Name (e.g., HDFC Mutual Fund)")
        if st.button("Create Folio"):
            if new_folio_num and amc_name:
                folio_id = db.add_folio(client_id, new_folio_num, amc_name)
                st.success(f"Folio {new_folio_num} created!")
                st.rerun()
            else:
                st.error("Folio number and AMC name are required.")
                return
    
    if folio_id:
        st.divider()
        with st.form("transaction_form", clear_on_submit=True):
            # Fetch schemes for selection
            schemes_df = db.run_query("SELECT * FROM schemes")
            if schemes_df.empty:
                st.error("No schemes found in database. Please add schemes first (e.g., via MFU API).")
                # Temporary manual scheme addition for demo
                st.info("Tip: You can add schemes directly to the 'schemes' table for testing.")
                return

            scheme_options = {row['scheme_name']: row['scheme_id'] for _, row in schemes_df.iterrows()}
            scheme_name = st.selectbox("Select Scheme", list(scheme_options.keys()))
            scheme_id = scheme_options[scheme_name]
            
            t_type = st.selectbox("Transaction Type", ["PURCHASE", "REDEMPTION", "SIP", "STP", "SWP"])
            date = st.date_input("Transaction Date", value=datetime.now())
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
            nav = st.number_input("NAV at Transaction", min_value=0.0, step=0.0001, format="%.4f")
            
            if nav > 0:
                units = amount / nav
                st.write(f"Estimated Units: {units:.4f}")
            else:
                units = 0.0

            t_submitted = st.form_submit_button("Submit Transaction")
            
            if t_submitted:
                if amount <= 0 or nav <= 0:
                    st.error("Amount and NAV must be greater than zero.")
                else:
                    db.add_transaction(folio_id, scheme_id, date.strftime('%Y-%m-%d'), t_type, amount, units, nav)
                    st.success("Transaction recorded successfully!")

def render_notes_section(db, investor_id):
    """UI for viewing and adding notes."""
    st.subheader("Investor Notes")
    
    # 1. Add Note Form
    with st.expander("Add New Note"):
        with st.form("new_note_form", clear_on_submit=True):
            content = st.text_area("Note Content")
            category = st.selectbox("Category", ["General", "Meeting Minutes", "Complaint", "Advice Given"])
            if st.form_submit_button("Save Note"):
                if content:
                    db.add_note(investor_id, content, category)
                    st.success("Note saved!")
                    st.rerun()
                else:
                    st.error("Note content cannot be empty.")

    # 2. Search Notes
    search_query = st.text_input("Search through notes...", key="note_search")
    
    # 3. Display Notes
    if search_query:
        notes_df = db.search_notes(search_query)
        # Filter for current investor if not searching globally
        notes_df = notes_df[notes_df['investor_id'] == investor_id]
    else:
        notes_df = db.get_notes(investor_id)

    if not notes_df.empty:
        for _, note in notes_df.iterrows():
            with st.container(border=True):
                st.caption(f"{note['created_at']} | {note['category']}")
                st.write(note['content'])
    else:
        st.info("No notes found.")

def render_tasks_section(db, investor_id):
    """UI for managing tasks."""
    st.subheader("Task Management")

    # 1. Add Task Form
    with st.expander("Add New Task"):
        with st.form("new_task_form", clear_on_submit=True):
            desc = st.text_input("Task Description")
            due_date = st.date_input("Due Date")
            priority = st.selectbox("Priority", ["High", "Med", "Low"], index=1)
            if st.form_submit_button("Create Task"):
                if desc:
                    db.add_task(investor_id, desc, due_date.strftime('%Y-%m-%d'), priority=priority)
                    st.success("Task created!")
                    st.rerun()
                else:
                    st.error("Task description is required.")

    # 1.1 Recurring/Standard Tasks for MFDs
    with st.expander("Schedule Standard MFD Task"):
        col1, col2 = st.columns([2, 1])
        with col1:
            task_type = st.selectbox("Standard Task Type", ["Annual Portfolio Review", "Quarterly KYC Update", "Nomination Review"])
        with col2:
            if st.button("Schedule Now"):
                if task_type == "Annual Portfolio Review":
                    # Due in 1 year
                    due = datetime.now().replace(year=datetime.now().year + 1)
                elif task_type == "Quarterly KYC Update":
                    # Due in 3 months
                    month = (datetime.now().month + 2) % 12 + 1
                    year = datetime.now().year + (datetime.now().month + 2) // 12
                    due = datetime.now().replace(year=year, month=month)
                else:
                    due = datetime.now()
                
                db.add_task(investor_id, task_type, due.strftime('%Y-%m-%d'), priority="Med")
                st.success(f"Scheduled: {task_type} for {due.strftime('%Y-%m-%d')}")
                st.rerun()

    # 2. List Tasks
    tasks_df = db.get_tasks(investor_id)
    if not tasks_df.empty:
        for _, task in tasks_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{task['description']}**")
                    st.caption(f"Due: {task['due_date']} | Priority: {task['priority']}")
                with col2:
                    new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Cancelled"], 
                                            index=["Pending", "In Progress", "Completed", "Cancelled"].index(task['status']),
                                            key=f"task_{task['id']}")
                    if new_status != task['status']:
                        db.update_task_status(task['id'], new_status)
                        st.rerun()
    else:
        st.info("No tasks for this investor.")
