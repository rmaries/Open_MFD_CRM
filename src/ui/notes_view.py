import streamlit as st

def render_notes_section(db, investor_id):
    """
    UI for viewing and adding timestamped investor notes.
    """
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

    # 2. Search UI
    search_query = st.text_input("Search through notes...", key="note_search")
    
    # 3. List display logic
    if search_query:
        notes_df = db.search_notes(search_query)
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
