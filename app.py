
import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import database as db

# Page Config
st.set_page_config(
    page_title="CYPAC Audiology — Stage A Checks",
    page_icon="🎧",
    layout="wide"
)

# Initialize Database
db.init_db()

# Master CYPAC 12 Room List
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

# Header Title
st.title("🎧 CYPAC Audiology — Stage A Equipment Console")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["📋 Live Check Form", "📌 Today's Board", "📊 Audit Dashboard", "⚠️ Fault Logbook"])

# Read QR Code Link Parameter (e.g., ?room=Orange+Room)
query_params = st.query_params
qr_room_param = query_params.get("room", None)

# =========================================================================
# PAGE 1: LIVE CHECK FORM (QR CODE AUTO-SELECT)
# =========================================================================
if page == "📋 Live Check Form":
    st.subheader("Submit Stage A Equipment Check")
    
    # Auto-match room from QR URL if present
    default_index = 0
    room_names = [r["room"] for r in CYPAC_ROOMS]
    if qr_room_param and qr_room_param in room_names:
        default_index = room_names.index(qr_room_param)
        st.success(f"🔗 Pre-selected room via QR Scan: **{qr_room_param}**")

    with st.form("stage_a_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            selected_room = st.selectbox("Select Clinic Room / Site *", room_names, index=default_index)
            
            # Lookup site matching selected room
            selected_site = next((item["site"] for item in CYPAC_ROOMS if item["room"] == selected_room), "CYPAC")
            
            status = st.radio(
                "Stage A Check Status *",
                ["Completed", "Not in Use", "Reporting Faulty Equipment"],
                index=0
            )
        
        with col2:
            clinician = st.text_input("Clinician Initials *", max_chars=5)
            check_date = st.date_input("Check Date", datetime.date.today())
            
        fault_desc = ""
        if status == "Reporting Faulty Equipment":
            fault_desc = st.text_area("Describe Equipment Fault Details *")
            
        submitted = st.form_submit_button("⚡ Save Check Record", use_container_width=True)
        
        if submitted:
            if not clinician:
                st.error("Please enter your initials before submitting.")
            elif status == "Reporting Faulty Equipment" and not fault_desc:
                st.error("Please describe the equipment fault.")
            else:
                db.save_check(
                    check_date.strftime("%Y-%m-%d"), 
                    selected_site, 
                    selected_room, 
                    status, 
                    clinician, 
                    fault_desc
                )
                st.success(f"✅ Record saved for {selected_room} [{status}]!")

# =========================================================================
# PAGE 2: TODAY'S LIVE STATUS BOARD (ALL 12 ROOMS)
# =========================================================================
elif page == "📌 Today's Board":
    st.subheader(f"CYPAC Status Board — {today_str}")
    
    df_today = db.get_today_checks(today_str)
    
    # 3 Column Card Layout
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
                
                if current_status == "Completed":
                    st.success(f"### {room}\n**Site:** {site} | **Status:** ✅ Completed\n\n*By:* {clinician}")
                elif current_status == "Not in Use":
                    st.warning(f"### {room}\n**Site:** {site} | **Status:** 🟡 Not in Use\n\n*By:* {clinician}")
                else:
                    st.error(f"### {room}\n**Site:** {site} | **Status:** 🔴 Faulty Equipment\n\n*By:* {clinician}")
            else:
                st.info(f"### {room}\n**Site:** {site} | **Status:** ⚪ Not Performed")

# =========================================================================
# PAGE 3: AUDIT DASHBOARD (BAA COMPLIANCE FORMULA)
# =========================================================================
elif page == "📊 Audit Dashboard":
    st.subheader("CYPAC Stage A Quality & Audit Analytics")
    
    df_all = db.get_all_checks()
    
    if df_all.empty:
        st.info("No audit records logged yet.")
    else:
        total_checks = len(df_all)
        completed = len(df_all[df_all["status"] == "Completed"])
        faulty = len(df_all[df_all["status"] == "Reporting Faulty Equipment"])
        not_in_use = len(df_all[df_all["status"] == "Not in Use"])
        
        # BAA Compliance Formula: (Completed + Faulty) / (Total - Not In Use)
        denominator = total_checks - not_in_use
        compliance_rate = ((completed + faulty) / denominator * 100) if denominator > 0 else 0
        
        # Metric Cards Banner
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Compliance Rate", f"{compliance_rate:.1f}%")
        m2.metric("Total Completed", completed)
        m3.metric("Reported Faults", faulty)
        m4.metric("Rooms Not In Use", not_in_use)
        
        st.divider()
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            fig = px.pie(
                df_all, 
                names="status", 
                title="Stage A Status Distribution",
                color="status",
                color_discrete_map={
                    "Completed": "#34C759",
                    "Not in Use": "#FFCC00",
                    "Reporting Faulty Equipment": "#FF3B30",
                    "Not Performed": "#8E8E93"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col_chart2:
            fig_site = px.histogram(
                df_all,
                x="site",
                color="status",
                title="Check Status by Site / Department",
                barmode="group"
            )
            st.plotly_chart(fig_site, use_container_width=True)

# =========================================================================
# PAGE 4: FAULT LOGBOOK
# =========================================================================
elif page == "⚠️ Fault Logbook":
    st.subheader("Active Equipment Issues")
    df_faults = db.get_open_faults()
    
    if df_faults.empty:
        st.success("🎉 No active equipment faults logged!")
    else:
        st.dataframe(
            df_faults[["id", "date_reported", "site", "room_name", "fault_details", "reported_by", "status"]], 
            use_container_width=True
        )
