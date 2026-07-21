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
room_names = [r["room"] for r in CYPAC_ROOMS]

# Header Title
st.title("🎧 CYPAC Audiology — Stage A Equipment Console")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["📋 Live Check Form", "📌 Today's Board", "📊 Audit Dashboard", "⚠️ Fault Logbook"])

# Read QR Code Link Parameter (e.g., ?room=Orange+Room)
query_params = st.query_params
qr_room_param = query_params.get("room", None)

# Handle QR Code pre-selection & Session State persistence
if "selected_room" not in st.session_state:
    if qr_room_param and qr_room_param in room_names:
        st.session_state.selected_room = qr_room_param
    else:
        st.session_state.selected_room = room_names[0]

# =========================================================================
# PAGE 1: LIVE CHECK FORM (FIXED ROOM SELECTION PERSISTENCE)
# =========================================================================
if page == "📋 Live Check Form":
    st.subheader("Submit Stage A Equipment Check")
    
    if qr_room_param and qr_room_param in room_names and st.session_state.selected_room != qr_room_param:
        st.session_state.selected_room = qr_room_param

    # Room selection and Status placed outside form to preserve selection seamlessly during re-renders
    col1, col2 = st.columns(2)
    
    with col1:
        # Find index of persistent room selection
        current_idx = room_names.index(st.session_state.selected_room) if st.session_state.selected_room in room_names else 0
        
        selected_room = st.selectbox(
            "Select Clinic Room / Site *", 
            room_names, 
            index=current_idx,
            key="room_selectbox"
        )
        # Update session state on change
        st.session_state.selected_room = selected_room
        
        selected_site = next((item["site"] for item in CYPAC_ROOMS if item["room"] == selected_room), "CYPAC")
        
        status = st.radio(
            "Stage A Check Status *",
            ["Completed", "Not in Use", "Reporting Faulty Equipment"],
            index=0,
            key="status_radio"
        )

    with col2:
        clinician = st.text_input("Clinician Initials *", max_chars=5, key="clinician_input")
        check_date = st.date_input("Check Date", datetime.date.today(), key="check_date_input")

    fault_desc = ""
    if status == "Reporting Faulty Equipment":
        st.warning(f"⚠️ Fault reported for **{selected_room}**. Please provide details below:")
        fault_desc = st.text_area("Describe Equipment Fault Details *", key="fault_desc_input")

    st.markdown("---")
    if st.button("⚡ Save Check Record", use_container_width=True, type="primary"):
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
            st.success(f"✅ Record saved for **{selected_room}** [{status}]!")

# =========================================================================
# PAGE 2: TODAY'S LIVE STATUS BOARD
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
        
        denominator = total_checks - not_in_use
        compliance_rate = ((completed + faulty) / denominator * 100) if denominator > 0 else 0
        
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
