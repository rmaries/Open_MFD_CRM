import streamlit as st
from datetime import datetime

def transaction_entry(db):
    """
    Renders the Investment Transaction entry interface.
    Implements a multi-step selection flow:
    1. Select Client -> 2. Select/Add CAN -> 3. Select/Add Folio -> 4. Enter Details.
    Automatically fetches current NAV if possible (mocked in this version).
    """
    st.header("📊 Investment Transaction Entry")
    
    # Step 1: Client Selection
    clients_df = db.get_all_clients()
    if clients_df.empty:
        st.warning("Please onboard a client first.")
        return

    client_options = {row['name']: row['client_id'] for _, row in clients_df.iterrows()}
    selected_client_name = st.selectbox("Select Client", list(client_options.keys()))
    client_id = client_options[selected_client_name]

    # 2. CAN Selection
    cans_df = db.get_client_cans(client_id)
    if cans_df.empty:
        st.warning("This client has no CAN numbers. Please add a CAN in the client's 'CAN Numbers' tab first.")
        return

    can_options = {row['can_number']: row['id'] for _, row in cans_df.iterrows()}
    selected_can_label = st.selectbox("Select CAN", list(can_options.keys()))
    can_id = can_options[selected_can_label]

    # 3. Folio Management
    folios_df = db.get_folios_for_can(can_id)
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
                folio_id = db.add_folio(can_id, new_folio_num, amc_name)
                st.success(f"Folio {new_folio_num} created!")
                st.rerun()
            else:
                st.error("Folio number and AMC name are required.")
                return
    
    # 4. Final Transaction Form
    if folio_id:
        st.divider()
        with st.form("transaction_form", clear_on_submit=True):
            schemes_df = db.run_query("SELECT * FROM schemes")
            if schemes_df.empty:
                st.error("No schemes found in database. Please add schemes first.")
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
