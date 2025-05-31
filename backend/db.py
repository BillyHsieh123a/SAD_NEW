import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables once at import
load_dotenv()

DB_USER_NAME     = os.getenv('DB_USER_NAME')
DB_USER_PASSWORD = os.getenv('DB_USER_PASSWORD')
DB_ADDRESS       = os.getenv('DB_ADDRESS')
DB_NAME          = os.getenv('DB_NAME')
DB_PORT          = os.getenv('DB_PORT')

def init_db_conn():
    """Test DB connection at startup (optional)."""
    try:
        conn = psycopg2.connect(
            dbname = DB_NAME,
            user = DB_USER_NAME,
            host = DB_ADDRESS,
            password = DB_USER_PASSWORD,
            port = DB_PORT
        )
        print("Connected to database!")
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")

def get_psql_conn():
    """Always return a new, open DB connection."""
    return psycopg2.connect(
        dbname = DB_NAME,
        user = DB_USER_NAME,
        host = DB_ADDRESS,
        password = DB_USER_PASSWORD,
        port = DB_PORT
    )