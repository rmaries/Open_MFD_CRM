import streamlit as st

def input_client_details(db):
    """
    Form to input client onboarding details.
    Handles field validation and database submission.
    """
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
