import urllib.request
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

def fetch_latest_navs() -> dict:
    """
    Fetches the latest NAVs from the official AMFI text file.
    
    Returns:
        dict: A mapping of {scheme_code: {'nav': nav_value, 'date': nav_date}}
              where scheme_code can be either the ISIN (preferred) or AMFI Scheme Code.
    """
    nav_data = {}
    try:
        response = urllib.request.urlopen(AMFI_URL)
        # Assuming the file is UTF-8 encoded, we decode it
        lines = response.read().decode('utf-8').splitlines()
        
        # AMFI NAV file format (semicolon separated):
        # Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
        # 0           1                              2                     3           4               5
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, headers, and section breaks (which don't have enough parts)
            if not line or line.startswith('Scheme Code') or ';' not in line:
                continue
                
            parts = line.split(';')
            if len(parts) >= 6:
                amfi_code = parts[0].strip()
                isin_code = parts[1].strip()
                nav_str = parts[4].strip()
                date_str = parts[5].strip()
                
                if nav_str and date_str:
                    try:
                        # Some NAVs might be "N.A."
                        if nav_str.upper() == 'N.A.':
                            continue
                            
                        nav_val = float(nav_str)
                        # The date in the file is typically DD-MMM-YYYY (e.g., 04-Mar-2026)
                        # We parse it and reformat it to YYYY-MM-DD for consistency in SQLite
                        try:
                            parsed_date = datetime.strptime(date_str, "%d-%b-%Y").strftime("%Y-%m-%d")
                        except ValueError:
                            # Fallback if the format changes unexpectedly
                            parsed_date = date_str
                            
                        data_point = {'nav': nav_val, 'date': parsed_date}
                        
                        # We index by both ISIN (primary) and AMFI code (fallback)
                        # ISINs are more robust but occasionally missing.
                        if isin_code and isin_code != '-':
                            nav_data[isin_code] = data_point
                        
                        if amfi_code and amfi_code != '-':
                            # We prefix AMFI codes slightly internally to avoid collisions? 
                            # Or just use them raw. Let's use raw as scheme_code could be either.
                            nav_data[amfi_code] = data_point
                            
                    except ValueError:
                        # Skip lines where NAV cannot be parsed
                        continue
                        
        logger.info(f"Successfully fetched and parsed {len(nav_data)} NAV entries from AMFI.")
        return nav_data
        
    except Exception as e:
        logger.error(f"Failed to fetch NAVs from AMFI: {e}")
        return {}
