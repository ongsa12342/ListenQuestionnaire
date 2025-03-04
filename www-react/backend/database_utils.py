import os
import logging
import time
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def require_env(var_name):
    """Retrieve an environment variable or raise an error if not set."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Required environment variable '{var_name}' is not set.")
    return value

class DBManager:
    """
    A modular database manager using SQLAlchemy for connecting to the MySQL database.
    """
    def __init__(self):
        # Load environment variables from the .env file in the project root
        load_dotenv()
        try:
            self.db_host = require_env("DB_HOST")
            self.db_port = require_env("DB_PORT")  # Keep as string for URI
            self.db_name = require_env("DB_NAME")
            self.db_user = require_env("DB_USER")
            self.db_password = require_env("DB_PASSWORD")
        except ValueError as e:
            logger.error(e)
            raise

        logger.info("All required environment variables are set:")
        logger.info(f"DB_HOST: {self.db_host}")
        logger.info(f"DB_PORT: {self.db_port}")
        logger.info(f"DB_NAME: {self.db_name}")
        logger.info(f"DB_USER: {self.db_user}")

        # Construct the SQLAlchemy connection URI
        self.connection_uri = (
            f"mysql+mysqlconnector://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4&collation=utf8mb4_general_ci"
        )
        self.engine = None

    def connect(self):
        """Create a SQLAlchemy engine to connect to the database."""
        try:
            self.engine = create_engine(
                self.connection_uri,
                echo=False,
                connect_args={"init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_general_ci"}
            )
            logger.info("SQLAlchemy engine created and connected to the database.")
            return self.engine
        except Exception as e:
            logger.error(f"Error creating SQLAlchemy engine: {e}")
            raise

    def close(self):
        """Dispose of the SQLAlchemy engine and close all connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("SQLAlchemy engine disposed, connection closed.")
    def read_query(self, query):
        """
        Execute a SQL SELECT query using pandas and return the result as a DataFrame.
        
        Parameters:
            query (str): The SQL query to execute.
            
        Returns:
            pd.DataFrame: The query result.
        """
        if not self.engine:
            raise Exception("Engine not connected. Call connect() first.")
        try:
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        
    def read_table(self, table, columns=None):
        """
        Read specific columns (or all columns) from a table into a DataFrame.
        
        Parameters:
            table (str): The name of the table to read.
            columns (list of str, optional): The columns to select. Defaults to None (select all).
            
        Returns:
            pd.DataFrame: The table contents (selected columns).
        """
        if not self.engine:
            raise Exception("Engine not connected. Call connect() first.")
        try:
            if columns and isinstance(columns, list):
                col_str = ", ".join(columns)
            else:
                col_str = "*"
            query = f"SELECT {col_str} FROM {table}"
            return self.read_query(query)
        except Exception as e:
            logger.error(f"Error reading table '{table}': {e}")
            raise

    def execute_query(self, query, params=None):
        """
        Execute a SQL query (INSERT, UPDATE, DELETE, or any non-select) without returning a DataFrame.
        Suitable for queries that don't need to return data.
        
        Parameters:
            query (str): The SQL query to execute.
            params (dict, optional): Parameter dictionary for parameterized queries.
            
        Returns:
            int: The number of rows affected (if applicable).
        """
        if not self.engine:
            raise Exception("Engine not connected. Call connect() first.")
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(query), params or {})
                return result.rowcount  # Number of rows inserted/updated/deleted
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def append_table(self, table_name, df, if_exists='append', index=False):
        """
        Append a Pandas DataFrame to a specific table in the database.
        
        Parameters:
            table_name (str): Name of the table to which data should be appended.
            df (pd.DataFrame): The DataFrame containing the data.
            if_exists (str): What to do if the table already exists. 
                             Common values: 'append', 'replace', 'fail'.
            index (bool): Whether to write the DataFrame index as a column.
        """
        if not self.engine:
            raise Exception("Engine not connected. Call connect() first.")
        try:
            df.to_sql(
                name=table_name,
                con=self.engine,
                if_exists=if_exists,
                index=index
            )
            logger.info(f"Data appended to table '{table_name}'.")
        except Exception as e:
            logger.error(f"Error appending DataFrame to table '{table_name}': {e}")
            raise