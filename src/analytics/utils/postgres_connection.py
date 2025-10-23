"""
PostgreSQL Connection Utility for Streamlit Applications
"""
import psycopg2
import pandas as pd
import os
from typing import Optional, Dict, Any
import streamlit as st

class PostgreSQLConnection:
    """PostgreSQL connection manager for Streamlit apps"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PostgreSQL connection
        
        Args:
            config: Database configuration dict with keys: host, port, database, user, password
        """
        if config:
            self.config = config
        else:
            # Default configuration from environment variables
            self.config = {
                'host': os.getenv('POSTGRES_HOST', 'aws-1-ap-southeast-1.pooler.supabase.com'),
                'port': int(os.getenv('POSTGRES_PORT', '6543')),
                'database': os.getenv('POSTGRES_DB', 'postgres'),
                'user': os.getenv('POSTGRES_USER', 'postgres.ltnxbmqzguhwwilvxfaj'),
                'password': os.getenv('POSTGRES_PASSWORD', 'mAdJUW85WcoYJiCc')
            }
        
        self.connection = None
    
    def connect(self) -> bool:
        """
        Establish database connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(**self.config)
            return True
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        Execute SQL query and return DataFrame
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return pd.DataFrame()
            
            df = pd.read_sql_query(query, self.connection, params=params)
            return df
            
        except Exception as e:
            st.error(f"❌ Query execution failed: {e}")
            return pd.DataFrame()
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.connect():
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.disconnect()
                return True
            return False
        except Exception as e:
            st.error(f"❌ Connection test failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get table information
        
        Args:
            table_name: Name of the table
            
        Returns:
            dict: Table information including row count and columns
        """
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return {}
            
            # Get row count
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_df = pd.read_sql_query(count_query, self.connection)
            row_count = count_df.iloc[0, 0] if not count_df.empty else 0
            
            # Get column info
            column_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """
            columns_df = pd.read_sql_query(column_query, self.connection, params=(table_name,))
            
            return {
                'row_count': row_count,
                'columns': columns_df.to_dict('records') if not columns_df.empty else []
            }
            
        except Exception as e:
            st.error(f"❌ Failed to get table info for {table_name}: {e}")
            return {}
    
    def get_database_summary(self) -> Dict[str, int]:
        """
        Get summary of all tables in database
        
        Returns:
            dict: Table names and their row counts
        """
        try:
            if not self.connection or self.connection.closed:
                if not self.connect():
                    return {}
            
            query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins - n_tup_del as row_count
            FROM pg_stat_user_tables
            ORDER BY row_count DESC
            """
            
            df = pd.read_sql_query(query, self.connection)
            return dict(zip(df['tablename'], df['row_count'])) if not df.empty else {}
            
        except Exception as e:
            st.error(f"❌ Failed to get database summary: {e}")
            return {}

# Global connection instance
_connection_instance = None

def get_postgres_connection(config: Optional[Dict[str, Any]] = None) -> PostgreSQLConnection:
    """
    Get PostgreSQL connection instance (singleton pattern)
    
    Args:
        config: Database configuration dict
        
    Returns:
        PostgreSQLConnection: Connection instance
    """
    global _connection_instance
    
    if _connection_instance is None:
        _connection_instance = PostgreSQLConnection(config)
    
    return _connection_instance

def execute_query_with_cache(query: str, params: tuple = None, ttl: int = 300) -> pd.DataFrame:
    """
    Execute query with Streamlit caching
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        ttl: Cache time-to-live in seconds
        
    Returns:
        pd.DataFrame: Query results
    """
    @st.cache_data(ttl=ttl)
    def _execute_cached_query(sql: str, param_tuple: tuple = None) -> pd.DataFrame:
        conn = get_postgres_connection()
        return conn.execute_query(sql, param_tuple)
    
    return _execute_cached_query(query, params)

def test_database_connection(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test database connection
    
    Args:
        config: Database configuration dict
        
    Returns:
        bool: True if connection successful
    """
    conn = get_postgres_connection(config)
    return conn.test_connection()

# Convenience functions for backward compatibility
def get_or_create_postgres_database():
    """
    Get PostgreSQL connection for Streamlit apps
    (Backward compatibility function)
    
    Returns:
        psycopg2.connection: Database connection
    """
    conn = get_postgres_connection()
    if conn.connect():
        return conn.connection
    return None

def execute_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Execute SQL query (backward compatibility)
    
    Args:
        sql: SQL query string
        params: Query parameters tuple
        
    Returns:
        pd.DataFrame: Query results
    """
    return execute_query_with_cache(sql, params)
