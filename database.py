import sqlite3
import os
from datetime import datetime
import pandas as pd

DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "cypac_checks.db")

def init_db():
    """Initializes the database schema with full audit fields."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_date TEXT NOT NULL,
            site TEXT NOT NULL,
            room_name TEXT NOT NULL,
            status TEXT NOT NULL,
            clinician TEXT NOT NULL,
            restocked_initials TEXT,
            cleaned_wiped TEXT,
            tymp_sn TEXT,
            tymp_2cc TEXT,
            tymp_b TEXT,
            tymp_oae TEXT,
            audio_hp TEXT,
            audio_in TEXT,
            audio_hpm TEXT,
            audio_inm TEXT,
            audio_bc TEXT,
            audio_sf TEXT,
            audio_hf_phones TEXT,
            audio_hfm TEXT,
            audio_vra TEXT,
            audio_music TEXT,
            audio_tablets TEXT,
            eclipse_hp TEXT,
            eclipse_in TEXT,
            eclipse_hpm TEXT,
            eclipse_inm TEXT,
            eclipse_bc TEXT,
            eclipse_imp TEXT,
            eclipse_cortical_sf TEXT,
            serial_matched TEXT,
            fault_found TEXT,
            fault_description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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

def save_check(check_data):
    """Saves or updates a detailed audit record."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    check_date = check_data["check_date"]
    room_name = check_data["room_name"]
    
    c.execute('SELECT id FROM daily_checks WHERE check_date = ? AND room_name = ?', (check_date, room_name))
    row = c.fetchone()
    
    if row:
        c.execute('''
            UPDATE daily_checks SET
                site=?, status=?, clinician=?, restocked_initials=?, cleaned_wiped=?,
                tymp_sn=?, tymp_2cc=?, tymp_b=?, tymp_oae=?,
                audio_hp=?, audio_in=?, audio_hpm=?, audio_inm=?, audio_bc=?, audio_sf=?,
                audio_hf_phones=?, audio_hfm=?, audio_vra=?, audio_music=?, audio_tablets=?,
                eclipse_hp=?, eclipse_in=?, eclipse_hpm=?, eclipse_inm=?, eclipse_bc=?, eclipse_imp=?, eclipse_cortical_sf=?,
                serial_matched=?, fault_found=?, fault_description=?, timestamp=?
            WHERE id=?
        ''', (
            check_data["site"], check_data["status"], check_data["clinician"], check_data["restocked_initials"], check_data["cleaned_wiped"],
            check_data["tymp_sn"], check_data["tymp_2cc"], check_data["tymp_b"], check_data["tymp_oae"],
            check_data["audio_hp"], check_data["audio_in"], check_data["audio_hpm"], check_data["audio_inm"], check_data["audio_bc"], check_data["audio_sf"],
            check_data["audio_hf_phones"], check_data["audio_hfm"], check_data["audio_vra"], check_data["audio_music"], check_data["audio_tablets"],
            check_data["eclipse_hp"], check_data["eclipse_in"], check_data["eclipse_hpm"], check_data["eclipse_inm"], check_data["eclipse_bc"], check_data["eclipse_imp"], check_data["eclipse_cortical_sf"],
            check_data["serial_matched"], check_data["fault_found"], check_data["fault_description"], datetime.now(), row[0]
        ))
    else:
        c.execute('''
            INSERT INTO daily_checks (
                check_date, site, room_name, status, clinician, restocked_initials, cleaned_wiped,
                tymp_sn, tymp_2cc, tymp_b, tymp_oae,
                audio_hp, audio_in, audio_hpm, audio_inm, audio_bc, audio_sf,
                audio_hf_phones, audio_hfm, audio_vra, audio_music, audio_tablets,
                eclipse_hp, eclipse_in, eclipse_hpm, eclipse_inm, eclipse_bc, eclipse_imp, eclipse_cortical_sf,
                serial_matched, fault_found, fault_description
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            check_date, check_data["site"], room_name, check_data["status"], check_data["clinician"], check_data["restocked_initials"], check_data["cleaned_wiped"],
            check_data["tymp_sn"], check_data["tymp_2cc"], check_data["tymp_b"], check_data["tymp_oae"],
            check_data["audio_hp"], check_data["audio_in"], check_data["audio_hpm"], check_data["audio_inm"], check_data["audio_bc"], check_data["audio_sf"],
            check_data["audio_hf_phones"], check_data["audio_hfm"], check_data["audio_vra"], check_data["audio_music"], check_data["audio_tablets"],
            check_data["eclipse_hp"], check_data["eclipse_in"], check_data["eclipse_hpm"], check_data["eclipse_inm"], check_data["eclipse_bc"], check_data["eclipse_imp"], check_data["eclipse_cortical_sf"],
            check_data["serial_matched"], check_data["fault_found"], check_data["fault_description"]
        ))
        
    if check_data["fault_found"] == "Y" and check_data["fault_description"]:
        c.execute('''
            INSERT INTO equipment_faults (date_reported, site, room_name, fault_details, reported_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (check_date, check_data["site"], room_name, check_data["fault_description"], check_data["clinician"]))
        
    conn.commit()
    conn.close()

def get_today_checks(check_date):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM daily_checks WHERE check_date = ?", conn, params=(check_date,))
    conn.close()
    return df

def get_all_checks():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM daily_checks ORDER BY check_date DESC", conn)
    conn.close()
    return df

def get_open_faults():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM equipment_faults WHERE status = 'Open' ORDER BY date_reported DESC", conn)
    conn.close()
    return df
