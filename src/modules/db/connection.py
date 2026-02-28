import sqlite3
import pandas as pd
import os

class ConnectionManager:
    """
    Handles raw SQLite connections and basic execution state.
    Centralizing this prevents connection leaks and ensures consistent URL handling.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self):
        """Returns a standard sqlite3 connection object."""
        return sqlite3.connect(self.db_path)

class BaseRepository:
    """
    The foundational class for all domain-specific repositories.
    Provides shared utilities for executing queries and fetching results as DataFrames.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection_manager = ConnectionManager(db_path)

    def get_connection(self):
        """Proxy method to get a new DB connection."""
        return self.connection_manager.get_connection()

    def run_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        Executes a SELECT query and returns the results as a Pandas DataFrame.
        This is the preferred way to fetch data for the UI and calculations.
        """
        conn = self.get_connection()
        try:
            return pd.read_sql_query(query, conn, params=params)
        finally:
            conn.close()
