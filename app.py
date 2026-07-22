import streamlit as st
import pandas as pd
import datetime
import io
import plotly.express as px
import database as db

# =========================================================================
# 1. PAGE CONFIGURATION (MUST BE THE FIRST STREAMLIT CALL EXECUTED)
# =========================================================================
st.set_page_config(
    page_title="CYPAC Audiology — Stage A Audit & Asset Console",
    page_icon="🎧",
    layout="wide"
)

# =========================================================================
# 2. APPLE HIG CUSTOM CSS THEME INJECTION
# =========================================================================
def apply_apple_theme():
    st.markdown("""
        <style>
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif !important;
            letter-spacing: -0.015em;
        }

        .stApp {
            background-color: #F5F5F7 !important;
        }

        .main .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }

        div[data-testid="metric-container"] {
            background-color: #FFFFFF !important;
            border-radius: 18px !important;
            padding: 18px 22px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04) !important;
            border: 1px solid rgba(0, 0, 0, 0.04) !important;
            transition: transform 0.2s ease;
        }
        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
        }
        
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #1D1D1F !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            color: #8E8E93 !important;
            text-transform: uppercase;
        }

        div[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border-radius: 16px !important;
            border: 1px solid rgba(0, 0, 0, 0.05) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02) !important;
            margin-bottom: 14px !important;
            overflow: hidden;
        }

        .stButton > button {
            border-radius: 12px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            background-color: #007AFF !important;
            color: #FFFFFF !important;
            border: none !important;
            padding: 0.65rem 1.4rem !important;
            box-shadow: 0 3px 10px rgba(0, 122, 255, 0.25) !important;
        }

        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="textarea"] > div {
            border-radius: 12px !important;
            border: 1px solid #D1D1D6 !important;
            background-color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #F2F2F7 !important;
            border-right: 1px solid #E5E5EA !important;
        }

        div[data-testid="stDataFrame"] {
            background-color: #FFFFFF !important;
            border-radius: 16px !important;
            padding: 8px !important;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03) !important;
            border: 1px solid rgba(0, 0, 0, 0.05) !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_apple_theme()

# =========================================================================
# 3. INITIALIZATION & CONSTANTS
# =========================================================================
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

st.title("🎧 CYPAC Audiology — Stage A Audit & Asset Console")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "📋 Live Check Form", 
    "📌 Today's Board", 
    "📦 Asset Register",
    "🔄 Move Equipment",
    "⚠️ Fault Logbook", 
    "📅 Calibration Tracker", 
    "📊 Audit Dashboard"
])

# Read QR Code Link Parameter (e.g., ?room=Orange+Room)
query_params = st.query_params
qr_room_param = query_params.get("room", None)

if "selected_room" not in st.session_state:
    if qr_room_param and qr_room_param in room_names:
        st.session_state.selected_room = qr_room_param
    else:
        st.session_state.selected_room = room_names[0]

# =========================================================================
# PAGE 1: LIVE CHECK FORM (FULL GRANULAR AUDIT CHECKLIST)
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
    df_transfers_today = db.get_today_transfers(today_str)
    
    cols = st.columns(3)
    for idx, r_info in enumerate(CYPAC_ROOMS):
        room = r_info["room"]
        site = r_info["site"]
        match = df_today[df_today["room_name"] == room] if not df_today.empty else pd.DataFrame()
        moved_here = df_transfers_today[df_transfers_today["to_room"] == room] if not df_transfers_today.empty else pd.DataFrame()
        
        col = cols[idx % 3]
        with col:
            if not match.empty:
                current_status = match.iloc[0]["status"]
                clinician = match.iloc[0]["clinician"]
                
                if current_status == "Completed":
                    st.success(f"### {room}\n**Site:** {site} | **Status:** ✅ Completed\n\n*By:* {clinician}")
                elif current_status == "Not in Use":
                    st.warning(f"### {room}\n**Site:** {site} | **Status:** 🟡 Not in Use\n\n*By:* {clinician}")
                else:
                    st.error(f"### {room}\n**Site:** {site} | **Status:** 🔴 Faulty Equipment\n\n*By:* {clinician}")
            else:
                st.info(f"### {room}\n**Site:** {site} | **Status:** ⚪ Not Performed")

            if not moved_here.empty:
                latest_move = moved_here.iloc[0]
                st.caption(f"📍 **{latest_move['device_name']}** moved here from **{latest_move['from_room']}**")

# =========================================================================
# PAGE 3: MASTER ASSET REGISTER
# =========================================================================
elif page == "📦 Asset Register":
    st.subheader("📦 CYPAC Master Equipment & Asset Register")
    
    df_assets = db.get_asset_register()
    
    if not df_assets.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Registered Assets", len(df_assets))
        m2.metric("In Home Room / Active", len(df_assets[df_assets["current_status"] == "In Home Room"]))
        m3.metric("Out for Repair", len(df_assets[df_assets["current_status"] == "Out for Repair"]))
        m4.metric("Calibration Alert (<30d)", len(df_assets[df_assets["Calibration Status"].str.contains("Due|OVERDUE", na=False)]))
        st.divider()

    col_f1, col_f2 = st.columns(2)
    search_query = col_f1.text_input("🔍 Search Asset Tag, Name, or Room", "")
    filter_status = col_f2.selectbox("Filter Status", ["All", "In Home Room", "Relocated", "Out for Repair"])

    df_filtered = df_assets.copy()
    if not df_filtered.empty:
        if search_query:
            df_filtered = df_filtered[
                df_filtered["asset_tag"].str.contains(search_query, case=False, na=False) |
                df_filtered["device_name"].str.contains(search_query, case=False, na=False) |
                df_filtered["home_room"].str.contains(search_query, case=False, na=False)
            ]
        if filter_status != "All":
            df_filtered = df_filtered[df_filtered["current_status"] == filter_status]
            
        st.dataframe(
            df_filtered[["asset_tag", "device_name", "home_site", "home_room", "current_status", "next_calibration", "Calibration Status", "notes"]], 
            use_container_width=True
        )
    else:
        st.info("No equipment registered yet.")

    st.markdown("---")
    with st.expander("➕ Add / Update Equipment Asset in Register"):
        with st.form("asset_register_form"):
            col1, col2 = st.columns(2)
            with col1:
                asset_tag = st.text_input("Asset Tag / Serial Number *", placeholder="e.g., TITAN-126398")
                device_name = st.text_input("Device Name / Model *", placeholder="e.g., Interacoustics Titan")
                home_site = st.selectbox("Home Site *", ["CYPAC", "Community", "Mobile"])
                home_room = st.selectbox("Home Room *", room_names)
            with col2:
                current_status = st.selectbox("Current Operational Status", ["In Home Room", "Relocated", "Out for Repair", "Retired"])
                last_cal_date = st.date_input("Last Calibration Date", datetime.date.today())
                next_cal_date = st.date_input("Next Calibration Due Date", last_cal_date + datetime.timedelta(days=365))
                notes = st.text_input("Notes / Equipment Specs", placeholder="e.g., Transducer SN: 3045501")

            if st.form_submit_button("⚡ Save Asset Record", type="primary", use_container_width=True):
                if not asset_tag or not device_name:
                    st.error("Please provide an Asset Tag/Serial No and Device Name.")
                else:
                    db.save_asset(asset_tag, device_name, home_site, home_room, current_status, last_cal_date.strftime("%Y-%m-%d"), next_cal_date.strftime("%Y-%m-%d"), notes)
                    st.success(f"✅ Saved asset **{device_name} ({asset_tag})**!")

# =========================================================================
# PAGE 4: MOVE EQUIPMENT
# =========================================================================
elif page == "🔄 Move Equipment":
    st.subheader("🔄 Track Titan & Portable Equipment Relocation")
    
    with st.form("transfer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            device_type = st.selectbox("Select Device Type *", ["Titan (Tympanometer / OAE)", "Eclipse ABR System", "Portable Audiometer", "VRA Tablet", "Other Transducer"])
            serial_no = st.text_input("Asset No / Serial No *", placeholder="e.g., Titan Asset #126398")
            from_room = st.selectbox("Moved FROM (Source Room) *", room_names, index=0)
        with col2:
            to_room = st.selectbox("Moved TO (Destination Room) *", room_names, index=1)
            clinician = st.text_input("Clinician Initials *", max_chars=5)
            reason = st.text_input("Reason / Notes (Optional)", placeholder="e.g., Primary room tymp faulty")

        if st.form_submit_button("⚡ Record Equipment Transfer", type="primary", use_container_width=True):
            if not serial_no or not clinician:
                st.error("Please provide both the Serial No and Clinician Initials.")
            elif from_room == to_room:
                st.error("Source and Destination rooms cannot be the same!")
            else:
                db.log_device_transfer(device_type, serial_no, from_room, to_room, clinician, reason)
                st.success(f"✅ Relocated **{device_type} ({serial_no})** from **{from_room}** ➔ **{to_room}**!")

    st.markdown("---")
    st.markdown("### 📍 Today's Equipment Movement Log")
    df_transfers = db.get_today_transfers(today_str)
    if df_transfers.empty:
        st.caption("No equipment transfers recorded today.")
    else:
        st.dataframe(df_transfers[["timestamp", "device_name", "serial_no", "from_room", "to_room", "clinician", "reason"]], use_container_width=True)

# =========================================================================
# PAGE 5: FAULT LOGBOOK & RELIABILITY ANALYTICS
# =========================================================================
elif page == "⚠️ Fault Logbook":
    st.subheader("Equipment Faults Management & Reliability Analytics")
    tab_active, tab_resolved, tab_analytics = st.tabs([
        "🔴 Active / In Repair", 
        "✅ Resolved History", 
        "📈 Fault Analytics & Audit"
    ])
    
    with tab_active:
        df_open = db.get_faults_by_status("Active")
        if df_open.empty:
            st.success("🎉 No active equipment faults logged!")
        else:
            st.warning(f"⚠️ **{len(df_open)} open issue(s)** pending resolution.")
            st.dataframe(df_open[["id", "date_reported", "site", "room_name", "fault_details", "reported_by", "status"]], use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🔧 Update Repair Status")
            with st.form("update_fault_form"):
                col_f1, col_f2 = st.columns(2)
                fault_id = col_f1.selectbox("Select Fault ID to Update", df_open["id"].tolist())
                new_status = col_f2.selectbox("Set New Status", ["In Repair", "Awaiting Parts", "Resolved"])
                resolution_notes = st.text_area("Resolution / Repair Notes", placeholder="e.g., Replacement transducer fitted by engineer")
                
                if st.form_submit_button("⚡ Update Status", type="primary"):
                    db.update_fault_status(fault_id, new_status, resolution_notes)
                    st.success(f"Fault #{fault_id} updated to **{new_status}**!")

    with tab_resolved:
        df_resolved = db.get_faults_by_status("Resolved")
        if df_resolved.empty:
            st.info("No resolved faults on record yet.")
        else:
            st.dataframe(df_resolved, use_container_width=True)

    with tab_analytics:
        st.markdown("### 📊 Equipment Reliability & Failure Analytics")
        df_all_faults = db.get_all_faults_data()
        
        if df_all_faults.empty:
            st.info("No fault records available for analysis yet.")
        else:
            total_faults = len(df_all_faults)
            open_faults = len(df_all_faults[df_all_faults["status"] != "Resolved"])
            resolved_faults = len(df_all_faults[df_all_faults["status"] == "Resolved"])
            
            df_resolved_only = df_all_faults[df_all_faults["status"] == "Resolved"].copy()
            avg_repair_days = 0
            if not df_resolved_only.empty and "date_resolved" in df_resolved_only.columns:
                df_resolved_only["reported_dt"] = pd.to_datetime(df_resolved_only["date_reported"])
                df_resolved_only["resolved_dt"] = pd.to_datetime(df_resolved_only["date_resolved"])
                df_resolved_only["repair_duration"] = (df_resolved_only["resolved_dt"] - df_resolved_only["reported_dt"]).dt.days
                avg_repair_days = df_resolved_only["repair_duration"].mean()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Faults Logged", total_faults)
            m2.metric("Active / Pending", open_faults, delta_color="inverse")
            m3.metric("Resolved Issues", resolved_faults)
            m4.metric("Avg Repair Time (MTTR)", f"{avg_repair_days:.1f} Days")
            
            st.divider()

            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                room_counts = df_all_faults["room_name"].value_counts().reset_index()
                room_counts.columns = ["Room Name", "Fault Count"]
                fig_rooms = px.bar(
                    room_counts, 
                    x="Fault Count", 
                    y="Room Name", 
                    orientation="h",
                    title="🔥 Equipment Faults by Clinic Room / Site",
                    color="Fault Count",
                    color_continuous_scale="Reds"
                )
                fig_rooms.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_rooms, use_container_width=True)

            with col_chart2:
                fig_status = px.pie(
                    df_all_faults,
                    names="status",
                    title="📊 Fault Status Distribution",
                    color="status",
                    color_discrete_map={
                        "Open": "#FF3B30",
                        "Awaiting Parts": "#FF9500",
                        "In Repair": "#5856D6",
                        "Resolved": "#34C759"
                    }
                )
                st.plotly_chart(fig_status, use_container_width=True)

# =========================================================================
# PAGE 6: CALIBRATION TRACKER
# =========================================================================
elif page == "📅 Calibration Tracker":
    st.subheader("Annual Equipment Calibration Tracker")
    
    with st.expander("➕ Register Device / Update Calibration Date"):
        with st.form("cal_form"):
            c1, c2 = st.columns(2)
            dev_name = c1.text_input("Device Name", placeholder="e.g., Interacoustics Titan")
            ser_no = c2.text_input("Asset / Serial Number", placeholder="e.g., 126398")
            cal_room = c1.selectbox("Assigned Room", room_names)
            last_cal_date = c2.date_input("Last Calibration Date", datetime.date.today())
            
            if st.form_submit_button("Save Calibration Record"):
                db.add_calibration_record(dev_name, ser_no, cal_room, last_cal_date.strftime("%Y-%m-%d"))
                st.success(f"Registered calibration record for {dev_name} ({ser_no})!")

    st.markdown("### 📋 Annual Calibration Schedule")
    df_cal = db.get_calibration_records()
    if df_cal.empty:
        st.info("No equipment calibration records registered yet.")
    else:
        st.dataframe(df_cal[["device_name", "serial_no", "room_name", "last_calibration", "next_calibration", "Days Remaining", "Calibration Alert"]], use_container_width=True)

# =========================================================================
# PAGE 7: AUDIT DASHBOARD & EXCEL EXPORT
# =========================================================================
elif page == "📊 Audit Dashboard":
    st.subheader("CYPAC Stage A Quality & Management Analytics")
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

        # EXCEL EXPORT BUTTON
        st.markdown("### 📥 Download Management Audit Reports")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_all.to_excel(writer, sheet_name="Daily Audit Checks", index=False)
            db.get_asset_register().to_excel(writer, sheet_name="Asset Register", index=False)
            db.get_all_faults_data().to_excel(writer, sheet_name="Equipment Faults", index=False)

        st.download_button(
            label="📊 Download Master Audit Workbook (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"CYPAC_StageA_Audit_Export_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

        st.markdown("---")
        st.markdown("### 🔍 Full Master Audit Dataset")
        st.dataframe(df_all, use_container_width=True)
