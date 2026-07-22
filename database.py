import datetime
import streamlit as st
import pandas as pd
from db import CalibrationDatabase, db

# ==============================================================================
# 1. PAGE CONFIGURATION & STYLING
# ==============================================================================

st.set_page_config(
    page_title="CYPAC Stage A Calibration Tracker",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stApp { background-color: #0f172a !important; }
        html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, label {
            color: #ffffff !important;
        }
        .stTextInput label, .stSelectbox label, .stTextArea label, .stNumberInput label {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        .card-status-pass {
            background-color: #064e3b; border: 1px solid #10b981;
            border-radius: 8px; padding: 12px; color: #a7f3d0 !important;
            text-align: center; font-weight: bold;
        }
        .card-status-fail {
            background-color: #7f1d1d; border: 1px solid #ef4444;
            border-radius: 8px; padding: 12px; color: #fecaca !important;
            text-align: center; font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. APP INITIALIZATION
# ==============================================================================

# Explicit database schema initialization (fixed line 109 equivalent)
db._init_db()

today_str = datetime.date.today().strftime("%Y-%m-%d")

# Header Section
st.title("🩺 CYPAC Stage A Calibration & Room Health Tracker")
st.caption(f"System Operational Date: {today_str} | Clinical Audit & Quality Assurance Matrix")
st.divider()

# ==============================================================================
# 3. NAVIGATION & TABS
# ==============================================================================

tab_checks, tab_history, tab_faults, tab_audit = st.tabs([
    "📝 DAILY STAGE A CHECK",
    "📊 TODAY'S LOGS & HISTORY",
    "⚠️ FAULT & REPAIR LIFECYCLE",
    "📜 SYSTEM AUDIT LOGS"
])

# ------------------------------------------------------------------------------
# TAB 1: DAILY STAGE A CHECK FORM
# ------------------------------------------------------------------------------
with tab_checks:
    st.subheader("New Clinical Stage A Inspection Form")
    
    with st.form("stage_a_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            clinician_name = st.text_input("Clinician / Tester Name:", placeholder="e.g., J. Smith")
            room_id = st.selectbox("Clinic Room ID:", [
                "Room 1 (Main VRA)", 
                "Room 2 (Paediatric)", 
                "Room 3 (Adult Audiometry)", 
                "Room 4 (Tympanometry/OAE)"
            ])
            equipment_id = st.text_input("Equipment / Audiometer Serial No:", placeholder="e.g., AUD-2026-X")
        
        with col2:
            visual_check = st.selectbox("Visual Inspection (Cables, Headphones, Transducers):", ["PASS", "FAIL"])
            listening_check = st.selectbox("Listening Check (Signal Purity & Frequency Accuracy):", ["PASS", "FAIL"])
            overall_status = "PASS" if (visual_check == "PASS" and listening_check == "PASS") else "FAIL"
            st.info(f"Calculated Stage A Status: **{overall_status}**")
            
        notes = st.text_area("Inspection Notes / Observations:", placeholder="Record any acoustic irregularities, wear, or fault details here...")
        
        submitted = st.form_submit_button("💾 Submit Daily Calibration Check")
        
        if submitted:
            if not clinician_name or not equipment_id:
                st.error("Please enter both Clinician Name and Equipment Serial Number before submitting.")
            else:
                check_id = db.save_stage_a_check(
                    room_id=room_id,
                    equipment_id=equipment_id,
                    clinician_name=clinician_name,
                    visual_inspection=visual_check,
                    listening_check=listening_check,
                    calibration_status=overall_status,
                    notes=notes
                )
                
                if overall_status == "FAIL":
                    db.log_fault(
                        room_id=room_id,
                        equipment_id=equipment_id,
                        fault_description=f"Stage A Fail: {notes if notes else 'Visual/Listening check failed.'}",
                        check_id=check_id,
                        reported_by=clinician_name
                    )
                    st.warning(f"Check #{check_id} saved as FAIL. An open fault ticket has been automatically logged.")
                else:
                    st.success(f"Stage A Check #{check_id} successfully saved as PASS!")
                st.rerun()

# ------------------------------------------------------------------------------
# TAB 2: TODAY'S CHECKS & HISTORICAL AUDIT
# ------------------------------------------------------------------------------
with tab_history:
    st.subheader(f"Checks Recorded Today ({today_str})")
    
    # Safely retrieve today's check entries
    df_today = db.get_today_checks(today_str)
    
    if df_today.empty:
        st.info("No Stage A checks recorded for today yet.")
    else:
        st.dataframe(df_today, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: FAULT & REPAIR LIFECYCLE
# ------------------------------------------------------------------------------
with tab_faults:
    st.subheader("Active Equipment & Room Faults")
    
    df_faults = db.get_open_faults()
    if df_faults.empty:
        st.success("All room equipment is fully operational! No active faults currently logged.")
    else:
        st.dataframe(df_faults, use_container_width=True)
        
        st.divider()
        st.write("### Resolve an Active Fault Ticket")
        fault_to_resolve = st.selectbox("Select Fault ID to Resolve:", df_faults["fault_id"].tolist())
        resolution_notes = st.text_area("Resolution Details / Repair Summary:")
        
        if st.button("✅ Mark Selected Fault as Resolved"):
            if not resolution_notes:
                st.error("Please provide resolution notes before closing the ticket.")
            else:
                db.resolve_fault(fault_to_resolve, resolution_notes)
                st.success(f"Fault #{fault_to_resolve} resolved and archived.")
                st.rerun()

# ------------------------------------------------------------------------------
# TAB 4: AUDIT LOGS
# ------------------------------------------------------------------------------
with tab_audit:
    st.subheader("System Access & Change Audit Trail")
    
    with db.get_connection() as conn:
        df_audit = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50", conn)
        
    if df_audit.empty:
        st.info("No audit logs recorded yet.")
    else:
        st.dataframe(df_audit, use_container_width=True)
