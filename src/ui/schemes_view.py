import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

def get_target_nav_date():
    """
    Determines the date for which the latest NAV should be available.
    Considers weekends and the ~9 PM update window for Indian Mutual Funds.
    """
    now = datetime.now()
    # Weekday: 0=Mon, ..., 4=Fri, 5=Sat, 6=Sun
    weekday = now.weekday()
    
    # Heuristic: AMFI updates usually happen by 9 PM IST for the current day.
    # Before 9 PM, we expect the previous working day's NAV.
    # After 9 PM, we expect today's NAV (if it's a working day).
    
    if weekday == 5: # Saturday
        # Expected is Friday
        return (now - timedelta(days=1)).date()
    elif weekday == 6: # Sunday
        # Expected is Friday
        return (now - timedelta(days=2)).date()
    elif weekday == 0: # Monday
        if now.hour < 21:
            return (now - timedelta(days=3)).date() # Previous Friday
        else:
            return now.date()
    else: # Tue-Fri
        if now.hour < 21:
            return (now - timedelta(days=1)).date()
        else:
            return now.date()


def render_schemes_management(db):
    st.header("📋 Scheme Management")
    st.write("View, add, and import mutual fund schemes.")

    tabs = st.tabs(["View Schemes", "Add Manual Scheme", "Bulk Import"])

    with tabs[0]:
        st.subheader("Current Schemes")
        
        # Auto-update NAVs if data is old. Skip if already updated in this session
        # or if the current DB data is already up-to-date for the target market date.
        schemes_df = db.get_all_schemes()
        needs_update = False
        
        target_date = get_target_nav_date()
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        if 'navs_updated' not in st.session_state:
            if not schemes_df.empty:
                # Check if the latest NAV in DB is older than the target market date
                latest_db_date_val = schemes_df['last_updated'].max()
                if isinstance(latest_db_date_val, str):
                    if latest_db_date_val[:10] < target_date_str:
                        needs_update = True
                else:
                    # In case it's not a string for some reason
                    needs_update = True
            else:
                # No schemes yet, maybe check anyway if we want pre-population? 
                # Actually if no schemes, update_scheme_navs() does nothing.
                pass
        
        if needs_update:
            with st.spinner(f"Checking for latest NAVs (Target: {target_date_str})..."):
                try:
                    updated = db.update_scheme_navs()
                    if updated > 0:
                        st.success(f"Updated {updated} NAVs.")
                        schemes_df = db.get_all_schemes() # Refresh after update
                    st.session_state.navs_updated = True
                except Exception as e:
                    st.error(f"Failed to update NAVs: {e}")
        
        if not schemes_df.empty:
            # Get the most recent date from the schemes to show in header
            # last_updated might be string or datetime
            latest_date = "Unknown"
            if 'last_updated' in schemes_df.columns and not schemes_df['last_updated'].dropna().empty:
                latest_date_val = schemes_df['last_updated'].max()
                if isinstance(latest_date_val, str):
                    # Handle both YYYY-MM-DD and YYYY-MM-DD HH:MM:SS
                    latest_date = latest_date_val[:10]
                else:
                    latest_date = latest_date_val.strftime("%Y-%m-%d")

            nav_header = f"Current NAV (as of {latest_date})"
            
            # Rename columns for better display
            display_df = schemes_df.rename(columns={
                'scheme_code': 'Scheme Code',
                'scheme_name': 'Scheme Name',
                'category': 'Category',
                'current_nav': nav_header
            })
            
            # Only show relevant columns
            cols_to_show = ['Scheme Code', 'Scheme Name', 'Category', nav_header]
            st.dataframe(display_df[cols_to_show], width='stretch', hide_index=True)
            
            # --- Edit/Delete Section ---
            st.divider()
            st.subheader("🛠️ Manage Schemes")
            selected_scheme_name = st.selectbox("Select a scheme to edit or delete", 
                                              options=[""] + display_df['Scheme Name'].tolist())
            
            if selected_scheme_name:
                scheme_row = display_df[display_df['Scheme Name'] == selected_scheme_name].iloc[0]
                scheme_id = schemes_df[schemes_df['scheme_name'] == selected_scheme_name].iloc[0]['scheme_id']
                
                with st.expander(f"Edit/Delete: {selected_scheme_name}", expanded=True):
                    with st.form(f"edit_scheme_{scheme_id}"):
                        new_code = st.text_input("Scheme Code", value=scheme_row['Scheme Code'])
                        new_name = st.text_input("Scheme Name", value=scheme_row['Scheme Name'])
                        new_cat = st.text_input("Category", value=scheme_row['Category'])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update Scheme"):
                                try:
                                    db.update_scheme(scheme_id, scheme_code=new_code, scheme_name=new_name, category=new_cat)
                                    st.success("Scheme updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        with col2:
                            # Delete is a bit tricky in form, let's use a separate column outside or a specific button
                            pass
                    
                    if st.button("🗑️ Delete Scheme", key=f"del_{scheme_id}"):
                        if st.warning("Are you sure you want to delete this scheme?"):
                            if st.button("Confirm Delete"):
                                try:
                                    db.delete_scheme(scheme_id)
                                    st.success("Scheme deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
        else:
            st.info("No schemes found. Add one manually or use Bulk Import.")

    with tabs[1]:
        st.subheader("Add New Scheme")
        with st.form("add_scheme_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                scheme_code = st.text_input("Scheme Code (e.g., ISIN)", help="Unique identifier for the scheme")
                scheme_name = st.text_input("Scheme Name")
            with col2:
                category = st.text_input("Category (e.g., Equity, Debt)")
                current_nav = st.number_input("Current NAV", min_value=0.0, step=0.0001, format="%.4f")
            
            submitted = st.form_submit_button("Add Scheme")
            if submitted:
                if not scheme_code or not scheme_name:
                    st.error("Scheme Code and Scheme Name are required.")
                else:
                    try:
                        db.add_scheme(scheme_code, scheme_name, category, current_nav)
                        st.success(f"Scheme '{scheme_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tabs[2]:
        st.subheader("Bulk Import Schemes")
        st.write("Upload a CSV or Excel file to import multiple schemes at once.")
        
        # Download template
        template_data = pd.DataFrame(columns=['scheme_code', 'scheme_name', 'category', 'current_nav'])
        template_data.loc[0] = ['INF209K01157', 'HDFC Top 100 Fund', 'Equity', 100.55]
        
        csv_template = template_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV Template",
            data=csv_template,
            file_name="scheme_import_template.csv",
            mime="text/csv",
        )

        uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Validation
                required_cols = ['scheme_code', 'scheme_name']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.write("### Preview Data")
                    st.dataframe(df.head(), width='stretch')
                    
                    if st.button("Confirm and Import"):
                        count = db.bulk_import_schemes(df)
                        st.success(f"Successfully imported/updated {count} schemes!")
                        st.rerun()
            except Exception as e:
                st.error(f"Error processing file: {e}")
