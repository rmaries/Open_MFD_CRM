import streamlit as st
import pandas as pd
import os
from modules.mfu_import import MFUTransactionImporter

def show_mfu_import_view(db):
    st.header("MFU Transaction Import")
    st.write("Upload MFU Entity Transaction Reports to automatically update client portfolios.")

    uploaded_file = st.file_uploader("Choose MFU Excel Report", type=['xlsx', 'xls'])

    if uploaded_file:
        # Save temp file
        temp_path = f"/tmp/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        importer = MFUTransactionImporter(db)
        
        try:
            with st.spinner("Parsing report..."):
                transactions = importer.parse_report(temp_path)
            
            if not transactions:
                st.warning("No valid transactions found in the report.")
                return

            st.write(f"Found **{len(transactions)}** potential transactions.")
            
            # Preview in a dataframe
            preview_df = pd.DataFrame(transactions)
            st.dataframe(preview_df[['order_number', 'can', 'folio', 'rta_code', 'type', 'amount', 'date']], use_container_width=True)

            if st.button("Start Import"):
                with st.spinner("Importing transactions..."):
                    results = importer.process_import(transactions)
                
                st.success(f"Import complete!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Imported", results['imported'])
                col2.metric("Duplicates Skipped", results['skipped_duplicate'])
                col3.metric("Errors", len(results['errors']))

                if results.get('auto_created_schemes', 0) > 0:
                    st.info(f"Automatically created {results['auto_created_schemes']} new schemes from the report.")

                if results['skipped_no_scheme'] > 0:
                    st.warning(f"Skipped {results['skipped_no_scheme']} transactions because the RTA Scheme Code was not mapped in the Schemes table.")
                
                if results['skipped_no_client'] > 0:
                    st.warning(f"Skipped {results['skipped_no_client']} transactions because the CAN was not found in the database.")

                if results['errors']:
                    with st.expander("View Errors"):
                        for err in results['errors']:
                            st.write(f"- {err}")
                
                # Cleanup temp file
                os.remove(temp_path)
                
        except Exception as e:
            st.error(f"Error processing report: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
