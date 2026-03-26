import urllib.request
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

def fetch_latest_navs() -> dict:
    """
    Fetches the latest NAVs from the official AMFI text file.
    
    Returns:
        dict: A mapping of {code: {'nav': nav_value, 'date': nav_date}}
              where code is any ISIN found in the row or the AMFI Scheme Code.
    """
    nav_data = {}
    try:
        response = urllib.request.urlopen(AMFI_URL)
        lines = response.read().decode('utf-8').splitlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Scheme Code') or ';' not in line:
                continue
                
            parts = line.split(';')
            if len(parts) >= 6:
                amfi_code = parts[0].strip()
                isin_growth_str = parts[1].strip()
                isin_reinv_str = parts[2].strip()
                nav_str = parts[4].strip()
                date_str = parts[5].strip()
                
                if nav_str and date_str:
                    try:
                        if nav_str.upper() == 'N.A.':
                            continue
                            
                        nav_val = float(nav_str)
                        try:
                            parsed_date = datetime.strptime(date_str, "%d-%b-%Y").strftime("%Y-%m-%d")
                        except ValueError:
                            parsed_date = date_str
                            
                        data_point = {'nav': nav_val, 'date': parsed_date}
                        
                        # 1. Index by AMFI Code
                        if amfi_code and amfi_code != '-':
                            nav_data[amfi_code] = data_point
                        
                        # 2. Extract and index all ISINs from both ISIN columns
                        # They can be separated by '/', ',', or space
                        all_isins = []
                        if isin_growth_str and isin_growth_str != '-':
                            all_isins.extend(re.split(r'[ /,\t]+', isin_growth_str))
                        if isin_reinv_str and isin_reinv_str != '-':
                            all_isins.extend(re.split(r'[ /,\t]+', isin_reinv_str))
                        
                        for isin in all_isins:
                            isin = isin.strip()
                            if isin and len(isin) >= 12: # Standard ISIN length
                                nav_data[isin] = data_point
                            
                    except ValueError:
                        continue
                        
        logger.info(f"Successfully fetched and parsed {len(nav_data)} codes from AMFI.")
        return nav_data
        
    except Exception as e:
        logger.error(f"Failed to fetch NAVs from AMFI: {e}")
        return {}
