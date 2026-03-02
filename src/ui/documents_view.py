import streamlit as st
import os
import base64

def render_documents_section(db, client_id):
    """
    UI for document management. 
    Includes uploading, viewing, and deleting files.
    """
    st.subheader("Client Documents")
    
    if "view_doc" not in st.session_state:
        st.session_state.view_doc = None
    
    # 1. Upload logic
    with st.expander("⬆️ Upload New Document"):
        with st.form("doc_upload_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'odt'])
            doc_type = st.selectbox("Document Type", ["Photo", "PAN Copy", "Masked Aadhaar", "Bank Proof", "Scanned Signature","Other"])
            if st.form_submit_button("Upload"):
                if uploaded_file:
                    db.add_document(client_id, uploaded_file, doc_type)
                    st.success(f"Uploaded successfully!")
                    st.rerun()

    # 2. Inline Viewer logic
    if st.session_state.view_doc is not None:
        doc = st.session_state.view_doc
        if doc['client_id'] == client_id:
            with st.container(border=True):
                vcol1, vcol2 = st.columns([5, 1])
                vcol1.write(f"### 👁️ Viewing: {doc['file_name']}")
                if vcol2.button("Close ✖️"):
                    st.session_state.view_doc = None
                    st.rerun()
                
                ext = os.path.splitext(doc['file_path'])[1].lower()
                doc_content = db.get_document_content(doc['doc_id'])
                
                if doc_content:
                    if ext in ['.png', '.jpg', '.jpeg']:
                        st.image(doc_content, use_container_width=True)
                    elif ext == '.pdf':
                        base64_pdf = base64.b64encode(doc_content).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.info("Download to view this file type.")

    # 3. Document Index listing
    docs_df = db.get_documents(client_id)
    if not docs_df.empty:
        for _, doc in docs_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1.8])
                with col1:
                    st.write(f"**{doc['file_name']}**")
                    st.caption(f"Type: {doc['doc_type']} | Uploaded: {doc['uploaded_at']}")
                with col2:
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button("👁️", key=f"view_{doc['doc_id']}"):
                            st.session_state.view_doc = doc
                            st.rerun()
                    with btn_col2:
                        doc_content = db.get_document_content(doc['doc_id'])
                        if doc_content:
                            st.download_button("💾", data=doc_content, file_name=doc['file_name'], key=f"dl_{doc['doc_id']}")
                    with btn_col3:
                        if st.button("🗑️", key=f"del_{doc['doc_id']}"):
                            db.delete_document(doc['doc_id'])
                            st.rerun()
    else:
        st.info("No documents uploaded.")
