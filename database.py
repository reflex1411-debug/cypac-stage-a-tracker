# Add this table inside init_db() in database.py
c.execute('''
    CREATE TABLE IF NOT EXISTS equipment_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT UNIQUE NOT NULL,
        device_name TEXT NOT NULL,
        home_site TEXT NOT NULL,
        home_room TEXT NOT NULL,
        current_status TEXT DEFAULT 'In Home Room',
        last_calibration TEXT,
        next_calibration TEXT,
        notes TEXT
    )
''')

# --- ASSET REGISTER HELPER FUNCTIONS ---
def save_asset(asset_tag, device_name, home_site, home_room, current_status, last_cal, next_cal, notes=""):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Insert or replace asset record
    c.execute('''
        INSERT INTO equipment_assets (asset_tag, device_name, home_site, home_room, current_status, last_calibration, next_calibration, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(asset_tag) DO UPDATE SET
            device_name=excluded.device_name,
            home_site=excluded.home_site,
            home_room=excluded.home_room,
            current_status=excluded.current_status,
            last_calibration=excluded.last_calibration,
            next_calibration=excluded.next_calibration,
            notes=excluded.notes
    ''', (asset_tag, device_name, home_site, home_room, current_status, last_cal, next_cal, notes))
    
    conn.commit()
    conn.close()

def get_asset_register():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM equipment_assets ORDER BY home_room ASC", conn)
    conn.close()
    
    if not df.empty and "next_calibration" in df.columns:
        today_dt = datetime.now().date()
        df["Days To Calibration"] = df["next_calibration"].apply(
            lambda x: (datetime.strptime(x, "%Y-%m-%d").date() - today_dt).days if x else None
        )
        def cal_status(days):
            if days is None: return "Unscheduled"
            if days < 0: return "🔴 OVERDUE"
            elif days <= 30: return "🟡 Due Soon (<30d)"
            else: return "🟢 Valid"
        df["Calibration Status"] = df["Days To Calibration"].apply(cal_status)
        
    return df
