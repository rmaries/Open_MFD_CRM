import streamlit as st

def render_notes_section(db, client_id):
    """
    UI for viewing and adding timestamped investor notes linked to a Client.
    """
    st.subheader("Investigation & Interaction Notes")
    
    # 1. Add Note Form
    with st.expander("Add New Note"):
        with st.form(f"new_note_form_{client_id}", clear_on_submit=True):
            content = st.text_area("Note Content", key=f"note_content_{client_id}")
            category = st.selectbox("Category", ["General", "Meeting Minutes", "Complaint", "Advice Given"], key=f"note_cat_{client_id}")
            if st.form_submit_button("Save Note"):
                if content:
                    db.add_note(client_id=client_id, content=content, category=category)
                    st.success("Note saved!")
                    st.rerun()
                else:
                    st.error("Note content cannot be empty.")

    # 2. Search UI (Optional filter)
    search_query = st.text_input("Search through notes...", key=f"note_search_{client_id}")
    
    # 3. List display logic
    if search_query:
        notes_df = db.search_notes(search_query)
        # Filter based on the current client
        notes_df = notes_df[notes_df['client_id'] == client_id]
    else:
        notes_df = db.get_notes(client_id=client_id)

    if not notes_df.empty:
        for _, note in notes_df.iterrows():
            with st.container(border=True):
                st.caption(f"{note['created_at']} | {note['category']}")
                st.write(note['content'])
    else:
        st.info("No notes found.")
