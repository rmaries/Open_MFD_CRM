import pandas as pd
import sqlite3
import logging
from .connection import BaseRepository
from ..nav_fetcher import fetch_latest_navs

logger = logging.getLogger(__name__)

class SchemeRepository(BaseRepository):
    """
    CRUD operations for mutual fund schemes.
    """
    def __init__(self, db_path: str, **kwargs):
        BaseRepository.__init__(self, db_path)

    def add_scheme(self, scheme_code, scheme_name, category=None, current_nav=None):
        """Adds a new scheme to the database. Automatically fetches NAV if not provided."""
        
        last_updated = None
        # Auto-fetch NAV if not provided or 0
        if not current_nav or current_nav == 0.0:
            try:
                latest_navs = fetch_latest_navs()
                if scheme_code in latest_navs:
                    current_nav = latest_navs[scheme_code]['nav']
                    last_updated = latest_navs[scheme_code]['date']
                    logger.info(f"Auto-fetched NAV for {scheme_code}: {current_nav} as of {last_updated}")
            except Exception as e:
                logger.error(f"Failed to auto-fetch NAV for {scheme_code}: {e}")

        query = '''
            INSERT INTO schemes (scheme_code, scheme_name, category, current_nav, last_updated)
            VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
        '''
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (scheme_code, scheme_name, category, current_nav, last_updated))
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: schemes.scheme_code" in str(e):
                raise Exception(f"Scheme code '{scheme_code}' already exists.")
            raise e
        finally:
            conn.close()

    def get_all_schemes(self) -> pd.DataFrame:
        """Fetches all schemes."""
        return self.run_query("SELECT * FROM schemes ORDER BY scheme_name ASC")

    def bulk_import_schemes(self, df: pd.DataFrame):
        """
        Imports multiple schemes from a DataFrame.
        Uses UPSERT logic based on scheme_code.
        """
        if df.empty:
            return 0

        query = '''
            INSERT INTO schemes (scheme_code, scheme_name, category, current_nav)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(scheme_code) DO UPDATE SET
                scheme_name = excluded.scheme_name,
                category = COALESCE(excluded.category, schemes.category),
                current_nav = COALESCE(excluded.current_nav, schemes.current_nav),
                last_updated = CURRENT_TIMESTAMP
        '''
        
        conn = self.get_connection()
        count = 0
        try:
            with conn:
                for _, row in df.iterrows():
                    conn.execute(query, (
                        str(row['scheme_code']),
                        str(row['scheme_name']),
                        str(row['category']) if 'category' in row and pd.notna(row['category']) else None,
                        float(row['current_nav']) if 'current_nav' in row and pd.notna(row['current_nav']) else None
                    ))
                    count += 1
            
            # After bulk import, trigger NAV update for schemes that might have missing NAVs
            self.update_scheme_navs()
            
            return count
        finally:
            conn.close()

    def update_scheme_navs(self):
        """
        Fetches latest NAVs from AMFI and updates the schemes table.
        """
        latest_navs = fetch_latest_navs()
        if not latest_navs:
            return 0
            
        conn = self.get_connection()
        updated_count = 0
        try:
            with conn:
                # We update schemes where we have a match in the latest_navs dict
                # We only update if the NAV or date is different (or last_updated is old)
                cursor = conn.cursor()
                cursor.execute("SELECT scheme_code FROM schemes")
                existing_codes = [row[0] for row in cursor.fetchall()]
                
                for code in existing_codes:
                    if code in latest_navs:
                        nav_val = latest_navs[code]['nav']
                        nav_date = latest_navs[code]['date']
                        
                        cursor.execute('''
                            UPDATE schemes 
                            SET current_nav = ?, last_updated = ? 
                            WHERE scheme_code = ?
                        ''', (nav_val, nav_date, code))
                        if cursor.rowcount > 0:
                            updated_count += 1
            return updated_count
        except Exception as e:
            logger.error(f"Error updating scheme NAVs: {e}")
            return 0
        finally:
            conn.close()
