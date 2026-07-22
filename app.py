import os
import sqlite3
from datetime import datetime, timedelta
import io
import pandas as pd
import streamlit as st
import plotly.express as px

# Import Pedalboard for VRA audio processing
try:
    from pedalboard import Pedalboard, HighpassFilter, PeakFilter, Compressor, Limiter
    from pedalboard.io import AudioFile
    PEDALBOARD_AVAILABLE = True
except ImportError:
    PEDALBOARD_AVAILABLE = False

# ==========================================
# 1. DATABASE BACKEND (SQLite)
# ==========================================

DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "cypac_checks.db")

def init_db():
    """Initializes database schema including all tables and auto-migrations."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Daily Checks Master Audit Table
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
    
    # Auto-migration for granular audit columns
    c.execute("PRAGMA table_info(daily_checks)")
    existing_cols = [row[1] for row in c.fetchall()]
    audit_columns = {
        "restocked_initials": "TEXT", "cleaned_wiped": "TEXT", "tymp_sn": "TEXT",
        "tymp_2cc": "TEXT", "tymp_b": "TEXT", "tymp_oae": "TEXT",
        "audio_hp": "TEXT", "audio_in": "TEXT", "audio_hpm": "TEXT", "audio_inm": "TEXT",
        "audio_bc": "TEXT", "audio_sf": "TEXT", "audio_hf_phones": "TEXT", "audio_hfm": "TEXT",
        "audio_vra": "TEXT", "audio_music": "TEXT", "audio_tablets": "TEXT",
        "eclipse_hp": "TEXT", "eclipse_in": "TEXT", "eclipse_hpm": "TEXT", "eclipse_inm": "TEXT",
        "eclipse_bc": "TEXT", "eclipse_imp": "TEXT", "eclipse_cortical_sf": "TEXT",
        "serial_matched": "TEXT", "fault_found": "TEXT"
    }
    for col_name, col_type in audit_columns.items():
        if col_name not in existing_cols:
            c.execute(f"ALTER TABLE daily_checks ADD COLUMN {col_name} {col_type}")

    # 2. Equipment Faults Table (Lifecycle tracking)
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment_faults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_reported TEXT NOT NULL,
            site TEXT NOT NULL,
            room_name TEXT NOT NULL,
            fault_details TEXT NOT NULL,
            reported_by TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            resolution_notes TEXT,
            date_resolved TEXT
        )
    ''')

    # 3. Equipment Calibration Tracking Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment_calibrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            serial_no TEXT NOT NULL,
            room_name TEXT NOT NULL,
            last_calibration TEXT NOT NULL,
            next_calibration TEXT NOT NULL,
            status TEXT DEFAULT 'Valid'
        )
    ''')

    # 4. Master Equipment Asset Register
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

    # 5. Equipment Relocation / Transfer Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transfer_date TEXT NOT NULL,
            device_name TEXT NOT NULL,
            serial_no TEXT,
            from_room TEXT NOT NULL,
            to_room TEXT NOT NULL,
            clinician TEXT NOT NULL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def save_check(check_data):
    """Saves or updates a detailed daily check record."""
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
            INSERT INTO equipment_faults (date_reported, site, room_name, fault_details, reported_by, status)
            VALUES (?, ?, ?, ?, ?, 'Open')
        ''', (check_date, check_data["site"], room_name, check_data["fault_description"], check_data["clinician"]))
        
    conn.commit()
    conn.close()

def update_fault_status(fault_id, new_status, notes=""):
    """Updates fault repair lifecycle status."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    resolved_date = datetime.now().strftime("%Y-%m-%d") if new_status == "Resolved" else None
    c.execute('''
        UPDATE equipment_faults 
        SET status = ?, resolution_notes = ?, date_resolved = ? 
        WHERE id = ?
    ''', (new_status, notes, resolved_date, fault_id))
    conn.commit()
    conn.close()

def get_faults_by_status(status_type="Active"):
    """Fetches active or resolved faults."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    if status_type == "Active":
        query = "SELECT * FROM equipment_faults WHERE status != 'Resolved' ORDER BY date_reported DESC"
    else:
        query = "SELECT * FROM equipment_faults WHERE status = 'Resolved' ORDER BY date_resolved DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_all_faults_data():
    """Fetches all faults for reliability analytics."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM equipment_faults ORDER BY date_reported DESC", conn)
    conn.close()
    return df

def add_calibration_record(device_name, serial_no, room_name, last_cal_str):
    """Adds or updates an annual equipment calibration record."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    last_dt = datetime.strptime(last_cal_str, "%Y-%m-%d")
    next_dt = last_dt + timedelta(days=365)
    next_cal_str = next_dt.strftime("%Y-%m-%d")
    
    c.execute('''
        INSERT INTO equipment_calibrations (device_name, serial_no, room_name, last_calibration, next_calibration)
        VALUES (?, ?, ?, ?, ?)
    ''', (device_name, serial_no, room_name, last_cal_str, next_cal_str))
    conn.commit()
    conn.close()

def get_calibration_records():
    """Fetches calibration schedule and calculates countdown days."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM equipment_calibrations ORDER BY next_calibration ASC", conn)
    conn.close()
    
    if not df.empty:
        today_dt = datetime.now().date()
        df["Days Remaining"] = df["next_calibration"].apply(
            lambda x: (datetime.strptime(x, "%Y-%m-%d").date() - today_dt).days
        )
        def alert_level(days):
            if days < 0: return "🔴 OVERDUE"
            elif days <= 30: return "🟡 Due Soon (<30 Days)"
            else: return "🟢 Valid"
        df["Calibration Alert"] = df["Days Remaining"].apply(alert_level)
    return df

def save_asset(asset_tag, device_name, home_site, home_room, current_status, last_cal, next_cal, notes=""):
    """Saves or updates an asset in the Master Register."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    """Retrieves all assets from the Master Register."""
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

def log_device_transfer(device_name, serial_no, from_room, to_room, clinician, reason=""):
    """Logs an equipment relocation event."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO equipment_transfers (transfer_date, device_name, serial_no, from_room, to_room, clinician, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%Y-%m-%d"), device_name, serial_no, from_room, to_room, clinician, reason))
    conn.commit()
    conn.close()

def get_today_transfers(transfer_date):
    """Retrieves equipment movements logged for today."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM equipment_transfers WHERE transfer_date = ? ORDER BY timestamp DESC", conn, params=(transfer_date,))
    conn.close()
    return df

def get_today_checks(check_date):
    """Retrieves daily check records logged for today."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM daily_checks WHERE check_date = ?", conn, params=(check_date,))
    conn.close()
    return df

def get_all_checks():
    """Retrieves complete historical audit log."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM daily_checks ORDER BY check_date DESC", conn)
    conn.close()
    return df

# ==========================================
# 2. AUDIO DSP PROCESSING (VRA Music)
# ==========================================

def process_vra_audio(input_file_path, output_file_path):
    """
    Applies high-pass filtering, presence boost, dynamic range compression,
    and peak limiting to ensure clean, constant-volume music for VRA testing.
    """
    if not PEDALBOARD_AVAILABLE:
        raise ImportError("pedalboard is required for audio processing. Run: pip install pedalboard")
        
    with AudioFile(input_file_path) as f:
        audio = f.read(f.frames)
        sr = f.samplerate

    # Audio DSP Chain
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=90.0),                  # Cut sub-bass rumble
        PeakFilter(cutoff_frequency_hz=2500.0, gain_db=2.5, q=1.0), # Enhance clarity
        Compressor(
            threshold_db=-20.0,   # Flatten dynamic volume range
            ratio=5.0,            # 5:1 compression ratio
            attack_ms=15.0,
            release_ms=120.0
        ),
        Limiter(threshold_db=-1.0) # Prevent clipping distortion
    ])

    processed_audio = board(audio, sr)

    with AudioFile(output_file_path, 'w', sr, processed_audio.shape[0]) as f:
        f.write(processed_audio)

    return output_file_path

# ==========================================
# 3. HELPER EXPORT FUNCTIONS
# ==========================================

def to_excel_download(df):
    """Converts a pandas DataFrame into an in-memory Excel file for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data_Export')
    return output.getvalue()

# ==========================================
# 4. STREAMLIT HIGH-CONTRAST UI & DASHBOARD
# ==========================================

def inject_high_contrast_theme():
    """Injects high-contrast CSS for clean, Apple-inspired legibility."""
    st.markdown("""
        <style>
        /* Base typography - dark Slate font */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
            color: #0f172a !important;
        }

        /* Bold, dark headers */
        h1, h2, h3, h4 {
            color: #0f172a !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }

        /* Metric card styling */
        div[data-testid="stMetric"] {
            background-color: #f8fafc !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            color: #475569 !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.7rem !important;
            font-weight: 800 !important;
            color: #0284c7 !important;
        }

        /* Buttons */
        .stButton > button {
            background-color: #0284c7 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1.25rem !important;
        }
        .stButton > button:hover {
            background-color: #0369a1 !important;
        }

        /* Clean borders for tables */
        .stDataFrame {
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="CYPAC Audiology & VRA Suite", page_icon="🎧", layout="wide")
    inject_high_contrast_theme()
    init_db()

    st.title("🎧 CYPAC Audiology Clinical Management & VRA Suite")
    
    # Navigation Sidebar
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Select Module:", [
        "🎵 VRA Music Processor",
        "📋 Daily Clinic Checks",
        "⚠️ Equipment Faults",
        "📅 Calibrations & Assets",
        "🔄 Device Transfers"
    ])

    # ----------------------------------------------------
    # MODULE 1: VRA MUSIC AUDIO PROCESSOR
    # ----------------------------------------------------
    if app_mode == "🎵 VRA Music Processor":
        st.header("🎵 VRA Music Audio Processor")
        st.caption("Optimizes audio files for VRA testing by filtering rumble, boosting presence, and compressing dynamic range for flat SPL output.")

        if not PEDALBOARD_AVAILABLE:
            st.error("⚠️ The `pedalboard` library is not installed. Run `pip install pedalboard` in your terminal to enable audio processing.")
        else:
            uploaded_file = st.file_uploader("Upload Music File (WAV/MP3)", type=["wav", "mp3", "flac"])
            
            if uploaded_file is not None:
                temp_dir = "temp_audio"
                os.makedirs(temp_dir, exist_ok=True)
                
                input_path = os.path.join(temp_dir, uploaded_file.name)
                output_path = os.path.join(temp_dir, f"vra_processed_{uploaded_file.name}.wav")
                
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.subheader("Original Track")
                st.audio(input_path)

                if st.button("🚀 Process Audio for VRA Audiometer"):
                    with st.spinner("Applying High-Pass Filter, Presence Boost & Dynamic Compression..."):
                        try:
                            processed_file = process_vra_audio(input_path, output_path)
                            st.success("✅ Processing complete!")
                            
                            st.subheader("Processed VRA Track (Constant Output)")
                            st.audio(processed_file)

                            with open(processed_file, "rb") as f:
                                st.download_button(
                                    label="💾 Download Processed VRA Audio",
                                    data=f,
                                    file_name=f"vra_processed_{uploaded_file.name}.wav",
                                    mime="audio/wav"
                                )
                        except Exception as e:
                            st.error(f"Error processing audio: {e}")

    # ----------------------------------------------------
    # MODULE 2: DAILY CLINIC CHECKS
    # ----------------------------------------------------
    elif app_mode == "📋 Daily Clinic Checks":
        st.header("📋 Daily Clinic Room Quality Assurance")
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        with st.form("daily_check_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                check_date = st.date_input("Check Date", datetime.now()).strftime("%Y-%m-%d")
                site = st.selectbox("Clinic Site", ["CYPAC Main", "Satellite North", "Satellite South"])
            with col2:
                room_name = st.selectbox("Room Name", [f"Room {i}" for i in range(1, 9)])
                clinician = st.text_input("Clinician Initials / Name")
            with col3:
                status = st.selectbox("Room Status", ["Pass", "Pass with Fault", "Fail / Out of Service"])
                restocked = st.text_input("Restocked Initials")

            st.markdown("---")
            st.subheader("Equipment Checks")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Tympanometer / OAE**")
                tymp_sn = st.text_input("Tymp S/N", "OK")
                tymp_2cc = st.selectbox("Tymp 2cc Cavity Check", ["Pass", "Fail", "N/A"])
                tymp_b = st.selectbox("Tymp Physical Status", ["Pass", "Fail", "N/A"])
                tymp_oae = st.selectbox("OAE Probe Check", ["Pass", "Fail", "N/A"])
            
            with c2:
                st.markdown("**Audiometer**")
                audio_hp = st.selectbox("Headphones (Right/Left)", ["Pass", "Fail", "N/A"])
                audio_in = st.selectbox("Insert Earphones", ["Pass", "Fail", "N/A"])
                audio_bc = st.selectbox("Bone Conductor", ["Pass", "Fail", "N/A"])
                audio_sf = st.selectbox("Soundfield Speakers / VRA", ["Pass", "Fail", "N/A"])

            with c3:
                st.markdown("**ABR / Eclipse / Other**")
                eclipse_hp = st.selectbox("Eclipse Headphones", ["Pass", "Fail", "N/A"])
                eclipse_in = st.selectbox("Eclipse Inserts", ["Pass", "Fail", "N/A"])
                cleaned = st.selectbox("Room Cleaned & Wiped", ["Yes", "No"])
                serial_matched = st.selectbox("Serials Matched", ["Yes", "No"])

            st.markdown("---")
            fault_found = st.radio("Was a fault identified today?", ["N", "Y"], horizontal=True)
            fault_description = st.text_area("Fault Description (If Y)", "")

            submit = st.form_submit_button("Save Daily Check Record")
            
            if submit:
                check_data = {
                    "check_date": check_date, "site": site, "room_name": room_name,
                    "status": status, "clinician": clinician, "restocked_initials": restocked,
                    "cleaned_wiped": cleaned, "tymp_sn": tymp_sn, "tymp_2cc": tymp_2cc,
                    "tymp_b": tymp_b, "tymp_oae": tymp_oae, "audio_hp": audio_hp,
                    "audio_in": audio_in, "audio_hpm": "Pass", "audio_inm": "Pass",
                    "audio_bc": audio_bc, "audio_sf": audio_sf, "audio_hf_phones": "Pass",
                    "audio_hfm": "Pass", "audio_vra": audio_sf, "audio_music": "Pass",
                    "audio_tablets": "Pass", "eclipse_hp": eclipse_hp, "eclipse_in": eclipse_in,
                    "eclipse_hpm": "Pass", "eclipse_inm": "Pass", "eclipse_bc": "Pass",
                    "eclipse_imp": "Pass", "eclipse_cortical_sf": "Pass",
                    "serial_matched": serial_matched, "fault_found": fault_found,
                    "fault_description": fault_description
                }
                save_check(check_data)
                st.success(f"✅ Check saved successfully for {room_name} ({check_date})!")

        st.markdown("---")
        st.subheader("Today's Submitted Checks")
        df_checks = get_today_checks(today_str)
        st.dataframe(df_checks, use_container_width=True)

        if not df_checks.empty:
            excel_data = to_excel_download(df_checks)
            st.download_button(
                label="📊 Export Today's Checks to Excel",
                data=excel_data,
                file_name=f"cypac_daily_checks_{today_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ----------------------------------------------------
    # MODULE 3: EQUIPMENT FAULTS
    # ----------------------------------------------------
    elif app_mode == "⚠️ Equipment Faults":
        st.header("⚠️ Equipment Fault & Repair Lifecycle Tracker")

        tab1, tab2, tab3 = st.tabs(["Active Faults", "Resolved Faults Log", "📊 Fault Analytics"])
        
        with tab1:
            df_active = get_faults_by_status("Active")
            if df_active.empty:
                st.info("🟢 No active equipment faults reported.")
            else:
                st.dataframe(df_active, use_container_width=True)
                
                st.subheader("Update Fault Repair Status")
                fault_id = st.number_input("Select Fault ID to Update", min_value=1, step=1)
                new_status = st.selectbox("New Status", ["Open", "Under Repair", "Resolved"])
                notes = st.text_area("Resolution / Engineering Notes")
                
                if st.button("Update Fault Status"):
                    update_fault_status(fault_id, new_status, notes)
                    st.success(f"Updated Fault ID #{fault_id} to {new_status}!")
                    st.rerun()

        with tab2:
            df_resolved = get_faults_by_status("Resolved")
            st.dataframe(df_resolved, use_container_width=True)

        with tab3:
            st.subheader("Equipment Reliability Analytics")
            df_all = get_all_faults_data()
            if not df_all.empty:
                fig = px.histogram(df_all, x="room_name", color="status", title="Fault Distribution by Room", barmode="group")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No fault history available to analyze.")

    # ----------------------------------------------------
    # MODULE 4: CALIBRATIONS & ASSETS
    # ----------------------------------------------------
    elif app_mode == "📅 Calibrations & Assets":
        st.header("📅 Annual Calibration & Asset Register")

        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Calibration Expiry Countdown")
            df_cal = get_calibration_records()
            if not df_cal.empty:
                st.dataframe(df_cal, use_container_width=True)
            else:
                st.info("No calibration records logged yet.")

        with col2:
            st.subheader("Add Calibration Entry")
            with st.form("cal_form"):
                dev_name = st.text_input("Device Name", "Inventis Audiometer")
                ser_no = st.text_input("Serial Number", "SN123456")
                rm_name = st.text_input("Room Name", "Room 1")
                cal_date = st.date_input("Calibration Date", datetime.now()).strftime("%Y-%m-%d")
                
                if st.form_submit_button("Log Calibration"):
                    add_calibration_record(dev_name, ser_no, rm_name, cal_date)
                    st.success("Calibration added!")
                    st.rerun()

    # ----------------------------------------------------
    # MODULE 5: DEVICE TRANSFERS
    # ----------------------------------------------------
    elif app_mode == "🔄 Device Transfers":
        st.header("🔄 Equipment Relocation & Transfer Log")

        with st.form("transfer_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                dev_name = st.text_input("Device Name", "Otosuite Tymp")
                ser_no = st.text_input("Serial Number", "TYMP-889")
            with c2:
                from_room = st.selectbox("From Room", [f"Room {i}" for i in range(1, 9)])
                to_room = st.selectbox("To Room", [f"Room {i}" for i in range(1, 9)])
            with c3:
                clinician = st.text_input("Logged By (Initials)")
                reason = st.text_input("Reason for Transfer", "Temporary replacement for repair")

            if st.form_submit_button("Log Relocation Event"):
                log_device_transfer(dev_name, ser_no, from_room, to_room, clinician, reason)
                st.success(f"Logged move of {dev_name} from {from_room} to {to_room}.")

        st.subheader("Today's Equipment Movements")
        today_str = datetime.now().strftime("%Y-%m-%d")
        df_transfers = get_today_transfers(today_str)
        st.dataframe(df_transfers, use_container_width=True)

if __name__ == "__main__":
    main()
