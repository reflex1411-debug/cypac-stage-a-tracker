import sqlite3
import os
from datetime import datetime
import pandas as pd

DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "cypac_checks.db")

def init_db():
    """Initializes the SQLite database directory and tables."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Audit Log Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_date TEXT NOT NULL,
            site TEXT NOT NULL,
            room_name TEXT NOT NULL,
            status TEXT NOT NULL,
            clinician TEXT NOT NULL,
            fault_description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Equipment Faults Logbook
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment_faults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_reported TEXT NOT NULL,
            site TEXT NOT NULL,
            room_name TEXT NOT NULL,
            fault_details TEXT NOT NULL,
            reported_by TEXT NOT NULL,
            status TEXT DEFAULT 'Open'
        )
    ''')
    conn.commit()
    conn.close()

def save_check(check_date, site, room_name, status, clinician, fault_desc=""):
    """Saves or updates a daily Stage A check record."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check for existing record today
    c.execute('SELECT id FROM daily_checks WHERE check_date = ? AND room_name = ?', (check_date, room_name))
    row = c.fetchone()
    
    if row:
        c.execute('''
            UPDATE daily_checks 
            SET status = ?, clinician = ?, fault_description = ?, timestamp = ?
            WHERE id = ?
        ''', (status, clinician, fault_desc, datetime.now(), row[0]))
    else:
        c.execute('''
            INSERT INTO daily_checks (check_date, site, room_name, status, clinician, fault_description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (check_date, site, room_name, status, clinician, fault_desc))
    
    # Auto-log issue into Equipment Faults
    if status == "Reporting Faulty Equipment" and fault_desc:
        c.execute('''
            INSERT INTO equipment_faults (date_reported, site, room_name, fault_details, reported_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (check_date, site, room_name, fault_desc, clinician))
        
    conn.commit()
    conn.close()

def get_today_checks(check_date):
    """Retrieves all checks logged for today."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM daily_checks WHERE check_date = ?", conn, params=(check_date,))
    conn.close()
    return df

def get_all_checks():
    """Retrieves historical audit data."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM daily_checks ORDER BY check_date DESC", conn)
    conn.close()
    return df

def get_open_faults():
    """Retrieves unresolved equipment faults."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM equipment_faults WHERE status = 'Open' ORDER BY date_reported DESC", conn)
    conn.close()
    return df
