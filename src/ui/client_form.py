import streamlit as st
import pandas as pd
from modules.bulk_import import create_template, parse_import_file, process_bulk_import

def input_client_details(db):
    """
    Form to input client onboarding details.
    Handles manual entry and bulk import via tabs.
    """
    st.header("Client Onboarding")
    
    tab_manual, tab_bulk = st.tabs(["👤 Manual Entry", "📁 Bulk Import"])
    
    with tab_manual:
        render_manual_entry(db)
        
    with tab_bulk:
        render_bulk_import(db)

def render_manual_entry(db):
    st.subheader("Single Client Onboarding")
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
                    client_id = db.add_client(
                        name=name, 
                        pan=pan if pan else None, 
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

def render_bulk_import(db):
    st.subheader("Bulk Client Onboarding")
    st.write("Upload an Excel, CSV, or ODS file to onboard multiple clients at once.")
    
    # Template Download
    template_data = create_template()
    st.download_button(
        label="📥 Download Template Excel",
        data=template_data,
        file_name="client_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.divider()
    
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "ods"])
    
    if uploaded_file is not None:
        df, error = parse_import_file(uploaded_file)
        
        if error:
            st.error(error)
        else:
            st.write("### Preview (First 5 rows)")
            st.dataframe(df.head(), width='stretch')
            
            if st.button("🚀 Process Bulk Import"):
                with st.spinner("Processing..."):
                    results = process_bulk_import(db, df)
                    
                    if results["success"] > 0:
                        st.success(f"Successfully onboarded {results['success']} clients!")
                    
                    if results["errors"]:
                        with st.expander("⚠️ Import Errors / Warnings"):
                            for err in results["errors"]:
                                st.warning(err)
                    
                    if results["success"] > 0:
                        st.balloons()
