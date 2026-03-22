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
        """Adds a new scheme to the database. Always attempts to fetch latest NAV from AMFI."""
        
        last_updated = None
        # Always attempt to fetch latest NAV from AMFI when adding, 
        # even if a current_nav is provided (to ensure it's the absolute latest)
        try:
            latest_navs = fetch_latest_navs()
            if scheme_code in latest_navs:
                current_nav = latest_navs[scheme_code]['nav']
                last_updated = latest_navs[scheme_code]['date']
                logger.info(f"Fetched latest NAV for {scheme_code}: {current_nav} as of {last_updated}")
        except Exception as e:
            logger.error(f"Failed to fetch NAV from AMFI for {scheme_code}: {e}")

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
        Fetches latest NAVs from AMFI and updates the schemes table if they differ.
        """
        latest_navs = fetch_latest_navs()
        if not latest_navs:
            return 0
            
        conn = self.get_connection()
        updated_count = 0
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT scheme_id, scheme_code, current_nav, last_updated FROM schemes")
                schemes = cursor.fetchall()
                
                for scheme_id, code, current_val, current_date in schemes:
                    if code in latest_navs:
                        new_nav = latest_navs[code]['nav']
                        new_date = latest_navs[code]['date']
                        
                        # Update if NAV or date is different
                        if new_nav != current_val or new_date != current_date:
                            cursor.execute('''
                                UPDATE schemes 
                                SET current_nav = ?, last_updated = ? 
                                WHERE scheme_id = ?
                            ''', (new_nav, new_date, scheme_id))
                            if cursor.rowcount > 0:
                                updated_count += 1
            return updated_count
        except Exception as e:
            logger.error(f"Error updating scheme NAVs: {e}")
            return 0
        finally:
            conn.close()

    def delete_scheme(self, scheme_id):
        """Deletes a scheme from the database."""
        query = 'DELETE FROM schemes WHERE scheme_id = ?'
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, (scheme_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    def update_scheme(self, scheme_id, scheme_code=None, scheme_name=None, category=None):
        """Updates scheme details."""
        updates = []
        params = []
        if scheme_code:
            updates.append("scheme_code = ?")
            params.append(scheme_code)
        if scheme_name:
            updates.append("scheme_name = ?")
            params.append(scheme_name)
        if category:
            updates.append("category = ?")
            params.append(category)
            
        if not updates:
            return False
            
        query = f"UPDATE schemes SET {', '.join(updates)} WHERE scheme_id = ?"
        params.append(scheme_id)
        
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                return cursor.rowcount > 0
        finally:
            conn.close()
