import sqlite3
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=1)
    conn.row_factory = sqlite3.Row
    return conn