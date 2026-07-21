import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import database as db

st.set_page_config(
    page_title="CYPAC Audiology — Stage A Audit & Calibration Console",
    page_icon="🎧",
    layout="wide"
)

db.init_db()

CYPAC_ROOMS = [
    {"site": "CYPAC", "room": "ABR room"},
    {"site": "CYPAC", "room": "Orange Room"},
    {"site": "CYPAC", "room": "Lime Room"},
    {"site": "CYPAC", "room": "Teal Room"},
    {"site": "CYPAC", "room": "NHSP Room"},
    {"site": "CYPAC", "room": "HUMB Room"},
    {"site": "CYPAC", "room": "PA Room"},
    {"site": "Community", "room": "Sunshine House"},
    {"site": "Community", "room": "Gracefield Gardens"},
    {"site": "CYPAC", "room": "Kal 2OK"},
    {"site": "CYPAC", "room": "Kal Booth"},
    {"site": "Mobile", "room": "Travelling ABR"},
]

today_str = datetime.date.today().strftime("%Y-%m-%d")
room_names = [r["room"] for r in CYPAC_ROOMS]

st.title("🎧 CYPAC Audiology — Stage A Audit & Management Console")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "📋 Live Check Form", 
    "📌 Today's Board", 
    "⚠️ Fault Logbook", 
    "📅 Calibration Tracker", 
    "📊 Audit Dashboard"
])

query_params = st.query_params
qr_room_param = query_params.get("room", None)

if "selected_room" not in st.session_state:
    if qr_room_param and qr_room_param in room_names:
        st.session_state.selected_room = qr_room_param
    else:
        st.session_state.selected_room = room_names[0]

# =========================================================================
# PAGE 1: GRANULAR AUDIT FORM
# =========================================================================
if page == "📋 Live Check Form":
    st.subheader("Stage A Equipment Checklist (Full Audit View)")
    
    if qr_room_param and qr_room_param in room_names and st.session_state.selected_room != qr_room_param:
        st.session_state.selected_room = qr_room_param

    col_top1, col_top2, col_top3 = st.columns(3)
    with col_top1:
        current_idx = room_names.index(st.session_state.selected_room) if st.session_state.selected_room in room_names else 0
        selected_room = st.selectbox("Select Clinic Room / Site *", room_names, index=current_idx, key="room_selectbox")
        st.session_state.selected_room = selected_room
        selected_site = next((item["site"] for item in CYPAC_ROOMS if item["room"] == selected_room), "CYPAC")
        
    with col_top2:
        clinician = st.text_input("Clinician Initials *", max_chars=5, key="clinician_input")
        restocked_initials = st.text_input("Room Restocked Initials", max_chars=5, key="restocked_input")

    with col_top3:
        check_date = st.date_input("Check Date", datetime.date.today(), key="check_date_input")
        status = st.selectbox("Overall Room Status *", ["Completed", "Not in Use", "Reporting Faulty Equipment"], index=0)

    st.markdown("---")

    with st.expander("🧹 1. Room Hygiene & Cleaning", expanded=True):
        cleaned_wiped = st.checkbox("Table & hard surfaces wiped down?", value=True)

    with st.expander("🔊 2. Tympanometer Checks", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        tymp_sn = c1.text_input("Titan Asset No / GSI SN", key="tymp_sn")
        tymp_2cc = "Y" if c2.checkbox("2cc Pass", value=True, key="tymp_2cc") else "N"
        tymp_b = "Y" if c3.checkbox("B Pass", value=True, key="tymp_b") else "N"
        tymp_oae = "Y" if c4.checkbox("OAE Pass", value=True, key="tymp_oae") else "N"

    with st.expander("🎧 3. Audiometer & Transducers", expanded=True):
        st.info("📌 **Transducer Serial Mapping:** HUMB: 3045501 | PA: 3045015 | NHSP: 2003234 | TEAL: 126400 | LIME: 126398 | ORANGE: 1937681 | KAL BOOTH BC: 304599 | 20K BC: 2003233")
        
        st.markdown("##### Standard Audiometer Checks")
        a1, a2, a3, a4, a5, a6 = st.columns(6)
        audio_hp = "Y" if a1.checkbox("HP", value=True) else "N"
        audio_in = "Y" if a2.checkbox("In", value=True) else "N"
        audio_hpm = "Y" if a3.checkbox("HP(M)", value=True) else "N"
        audio_inm = "Y" if a4.checkbox("In(M)", value=True) else "N"
        audio_bc = "Y" if a5.checkbox("BC", value=True) else "N"
        audio_sf = "Y" if a6.checkbox("SF", value=True) else "N"

        st.markdown("##### Astera Specific Checks")
        ast1, ast2, ast3, ast4, ast5 = st.columns(5)
        audio_hf_phones = "Y" if ast1.checkbox("HF Phones") else "N"
        audio_hfm = "Y" if ast2.checkbox("HF (M)") else "N"
        audio_vra = "Y" if ast3.checkbox("VRA") else "N"
        audio_music = "Y" if ast4.checkbox("Music Files") else "N"
        audio_tablets = "Y" if ast5.checkbox("Tablets") else "N"

    with st.expander("⚡ 4. Eclipse (ASSR / ABR / Cortical)", expanded=False):
        st.markdown("##### ABR Checks")
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        eclipse_hp = "Y" if e1.checkbox("ABR HP") else "N"
        eclipse_in = "Y" if e2.checkbox("ABR In") else "N"
        eclipse_hpm = "Y" if e3.checkbox("ABR HP(M)") else "N"
        eclipse_inm = "Y" if e4.checkbox("ABR In(M)") else "N"
        eclipse_bc = "Y" if e5.checkbox("ABR BC") else "N"
        eclipse_imp = "Y" if e6.checkbox("ABR Imp") else "N"

        st.markdown("##### Cortical Checks")
        eclipse_cortical_sf = "Y" if st.checkbox("Cortical SF") else "N"

    with st.expander("✅ 5. Verification & Fault Reporting", expanded=True):
        v1, v2 = st.columns(2)
        serial_matched = "Y" if v1.checkbox("Equipment Serial Numbers Checked & Match?", value=True) else "N"
        fault_found = "Y" if v2.checkbox("Fault Found?", value=(status == "Reporting Faulty Equipment")) else "N"
        fault_description = st.text_area("Notes / Fault Description", placeholder="e.g., Initially OEAs did not come through but no issues after changing tip")

    st.markdown("---")
    if st.button("⚡ Submit Complete Stage A Check", type="primary", use_container_width=True):
        if not clinician:
            st.error("Please enter Clinician Initials before submitting.")
        else:
            check_payload = {
                "check_date": check_date.strftime("%Y-%m-%d"),
                "site": selected_site,
                "room_name": selected_room,
                "status": status,
                "clinician": clinician,
                "restocked_initials": restocked_initials,
                "cleaned_wiped": "Y" if cleaned_wiped else "N",
                "tymp_sn": tymp_sn, "tymp_2cc": tymp_2cc, "tymp_b": tymp_b, "tymp_oae": tymp_oae,
                "audio_hp": audio_hp, "audio_in": audio_in, "audio_hpm": audio_hpm, "audio_inm": audio_inm, "audio_bc": audio_bc, "audio_sf": audio_sf,
                "audio_hf_phones": audio_hf_phones, "audio_hfm": audio_hfm, "audio_vra": audio_vra, "audio_music": audio_music, "audio_tablets": audio_tablets,
                "eclipse_hp": eclipse_hp, "eclipse_in": eclipse_in, "eclipse_hpm": eclipse_hpm, "eclipse_inm": eclipse_inm, "eclipse_bc": eclipse_bc, "eclipse_imp": eclipse_imp, "eclipse_cortical_sf": eclipse_cortical_sf,
                "serial_matched": serial_matched,
                "fault_found": fault_found,
                "fault_description": fault_description
            }
            db.save_check(check_payload)
            st.success(f"✅ Full Stage A Audit Record saved for **{selected_room}**!")

# =========================================================================
# PAGE 2: TODAY'S BOARD
# =========================================================================
elif page == "📌 Today's Board":
    st.subheader(f"CYPAC Status Board — {today_str}")
    df_today = db.get_today_checks(today_str)
    
    cols = st.columns(3)
    for idx, r_info in enumerate(CYPAC_ROOMS):
        room = r_info["room"]
        site = r_info["site"]
        match = df_today[df_today["room_name"] == room]
        
        col = cols[idx % 3]
        with col:
            if not match.empty:
                current_status = match.iloc[0]["status"]
                clinician = match.iloc[0]["clinician"]
                fault_flag = match.iloc[0]["fault_found"]
                
                if current_status == "Completed":
                    st.success(f"### {room}\n**Site:** {site} | **Status:** ✅ Completed\n\n*By:* {clinician}")
                elif current_status == "Not in Use":
                    st.warning(f"### {room}\n**Site:** {site} | **Status:** 🟡 Not in Use\n\n*By:* {clinician}")
                else:
                    st.error(f"### {room}\n**Site:** {site} | **Status:** 🔴 Faulty Equipment\n\n*By:* {clinician}")
            else:
                st.info(f"### {room}\n**Site:** {site} | **Status:** ⚪ Not Performed")

# =========================================================================
# PAGE 3: FAULT LOGBOOK (LIFECYCLE MANAGEMENT)
# =========================================================================
elif page == "⚠️ Fault Logbook":
    st.subheader("Equipment Faults Management & Lifecycle Tracker")
    
    tab_active, tab_resolved = st.tabs(["🔴 Awaiting Repair / In Progress", "✅ Resolved Faults History"])
    
    with tab_active:
        df_open = db.get_faults_by_status("Active")
        if df_open.empty:
            st.success("🎉 No active equipment faults logged!")
        else:
            st.warning(f"⚠️ **{len(df_open)} open issue(s)** pending resolution.")
            st.dataframe(df_open[["id", "date_reported", "site", "room_name", "fault_details", "reported_by", "status"]], use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🔧 Update Fault Repair Status")
            with st.form("update_fault_form"):
                col_f1, col_f2 = st.columns(2)
                fault_id = col_f1.selectbox("Select Fault ID to Update", df_open["id"].tolist())
                new_status = col_f2.selectbox("Set New Status", ["In Repair", "Awaiting Parts", "Resolved"])
                resolution_notes = st.text_area("Resolution / Repair Notes", placeholder="e.g., Replacement tip installed / Calibrated by engineer")
                
                if st.form_submit_button("Update Fault Status", type="primary"):
                    db.update_fault_status(fault_id, new_status, resolution_notes)
                    st.success(f"Fault #{fault_id} updated to **{new_status}**!")

    with tab_resolved:
        df_resolved = db.get_faults_by_status("Resolved")
        if df_resolved.empty:
            st.info("No resolved faults on record yet.")
        else:
            st.dataframe(df_resolved[["id", "date_reported", "date_resolved", "site", "room_name", "fault_details", "reported_by", "resolution_notes"]], use_container_width=True)

# =========================================================================
# PAGE 4: CALIBRATION TRACKER
# =========================================================================
elif page == "📅 Calibration Tracker":
    st.subheader("Annual Equipment Calibration Tracker")
    
    # Register New Device Calibration
    with st.expander("➕ Register Device / Update Calibration Date"):
        with st.form("cal_form"):
            c1, c2 = st.columns(2)
            dev_name = c1.text_input("Device Name", placeholder="e.g., Interacoustics Titan / Astera")
            ser_no = c2.text_input("Asset / Serial Number", placeholder="e.g., 126398")
            cal_room = c1.selectbox("Assigned Room", room_names)
            last_cal_date = c2.date_input("Last Calibration Date", datetime.date.today())
            
            if st.form_submit_button("Save Calibration Record"):
                db.add_calibration_record(dev_name, ser_no, cal_room, last_cal_date.strftime("%Y-%m-%d"))
                st.success(f"Registered calibration record for {dev_name} ({ser_no})!")

    # Display Calibration Schedule
    st.markdown("### 📋 Annual Calibration Schedule")
    df_cal = db.get_calibration_records()
    if df_cal.empty:
        st.info("No equipment calibration records registered yet.")
    else:
        st.dataframe(df_cal[["device_name", "serial_no", "room_name", "last_calibration", "next_calibration", "Days Remaining", "Calibration Alert"]], use_container_width=True)

# =========================================================================
# PAGE 5: AUDIT DASHBOARD
# =========================================================================
elif page == "📊 Audit Dashboard":
    st.subheader("CYPAC Stage A Quality & Management Audit Analytics")
    df_all = db.get_all_checks()
    
    if df_all.empty:
        st.info("No audit records logged yet.")
    else:
        total_checks = len(df_all)
        completed = len(df_all[df_all["status"] == "Completed"])
        faulty = len(df_all[df_all["status"] == "Reporting Faulty Equipment"])
        not_in_use = len(df_all[df_all["status"] == "Not in Use"])
        
        denominator = total_checks - not_in_use
        compliance_rate = ((completed + faulty) / denominator * 100) if denominator > 0 else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Compliance Rate", f"{compliance_rate:.1f}%")
        m2.metric("Total Completed", completed)
        m3.metric("Reported Faults", faulty)
        m4.metric("Rooms Not In Use", not_in_use)
        
        st.divider()
        st.markdown("### 🔍 Full Management Audit Log")
        st.dataframe(df_all, use_container_width=True)
