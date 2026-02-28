import streamlit as st

def render_can_management(db, client_id):
    """
    Sub-view for managing multiple CAN numbers for a single client profile.
    """
    st.subheader("Additional CAN Numbers")
    
    # 1. Registration Form
    with st.expander("➕ Add New CAN Number"):
        with st.form("add_can_form", clear_on_submit=True):
            new_can = st.text_input("CAN Number")
            if st.form_submit_button("Add CAN"):
                if new_can:
                    db.add_client_can(client_id, new_can)
                    st.success(f"CAN '{new_can}' added!")
                    st.rerun()
    
    # 2. Existing CAN List
    cans_df = db.get_client_cans(client_id)
    if not cans_df.empty:
        for _, can in cans_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{can['can_number']}**")
                    st.caption(f"Added on: {can['created_at']}")
                with col2:
                    if st.button("🗑️", key=f"del_can_{can['id']}"):
                        db.delete_client_can(can['id'])
                        st.rerun()
                
                # New: CAN-specific interactions
                from ui.notes_view import render_notes_section
                from ui.tasks_view import render_tasks_section
                
                c_tab1, c_tab2 = st.tabs(["CAN Notes", "CAN Tasks"])
                with c_tab1:
                    render_notes_section(db, can_id=can['id'])
                with c_tab2:
                    render_tasks_section(db, can_id=can['id'])
    else:
        st.info("No additional CAN numbers stored.")
