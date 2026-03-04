import pandas as pd
import io
import streamlit as st

def create_template():
    """Creates a template Excel file and returns it as bytes."""
    df = pd.DataFrame(columns=["Name *", "Phone *", "PAN", "Email", "MFU CAN"])
    # Add a sample row (optional, but helpful)
    # df.loc[0] = ["John Doe", "9876543210", "ABCDE1234F", "john@example.com", "1234567"]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Clients')
    
    return output.getvalue()

def parse_import_file(uploaded_file):
    """Parses Excel, CSV, or ODS file and returns a DataFrame."""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif file_extension == 'ods':
            df = pd.read_excel(uploaded_file, engine='odf')
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Normalize column names (remove * and strip whitespace)
        df.columns = [col.replace('*', '').strip() for col in df.columns]
        
        # Basic validation: Check mandatory columns
        required_cols = ["Name", "Phone"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return None, f"Missing required columns: {', '.join(missing_cols)}"
        
        return df, None
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"

def process_bulk_import(db, df):
    """Iterates through the DataFrame and adds clients to the database."""
    results = {"success": 0, "errors": []}
    
    for index, row in df.iterrows():
        name = str(row.get("Name", "")).strip()
        phone = str(row.get("Phone", "")).strip()
        pan = str(row.get("PAN", "")).strip() if pd.notna(row.get("PAN")) else None
        email = str(row.get("Email", "")).strip() if pd.notna(row.get("Email")) else None
        can = str(row.get("MFU CAN", "")).strip() if pd.notna(row.get("MFU CAN")) else None
        
        if not name or name == "nan" or not phone or phone == "nan":
            results["errors"].append(f"Row {index + 2}: Name and Phone are mandatory.")
            continue
            
        try:
            db.add_client(
                name=name,
                phone=phone,
                pan=pan.upper() if pan else None,
                email=email,
                can_number=can
            )
            results["success"] += 1
        except Exception as e:
            results["errors"].append(f"Row {index + 2} ({name}): {str(e)}")
            
    return results
