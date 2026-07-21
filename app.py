# 1. Update Navigation Radio in app.py
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "📋 Live Check Form", 
    "📌 Today's Board", 
    "📦 Asset Register",
    "⚠️ Fault Logbook", 
    "📅 Calibration Tracker", 
    "📊 Audit Dashboard"
])

# =========================================================================
# PAGE: MASTER ASSET REGISTER
# =========================================================================
if page == "📦 Asset Register":
    st.subheader("📦 CYPAC Master Equipment & Asset Register")
    
    df_assets = db.get_asset_register()
    
    # Key Summary Metrics
    if not df_assets.empty:
        m1, m2, m3, m4 = st.columns(4)
        total_assets = len(df_assets)
        in_service = len(df_assets[df_assets["current_status"] == "In Home Room"])
        out_repair = len(df_assets[df_assets["current_status"] == "Out for Repair"])
        cal_due = len(df_assets[df_assets["Calibration Status"].str.contains("Due|OVERDUE", na=False)])
        
        m1.metric("Total Registered Assets", total_assets)
        m2.metric("In Home Room / Active", in_service)
        m3.metric("Out for Repair", out_repair)
        m4.metric("Calibration Alert (<30d)", cal_due)
        st.divider()

    # Search & Filter Controls
    col_f1, col_f2 = st.columns(2)
    search_query = col_f1.text_input("🔍 Search by Asset Tag, Name, or Room", "")
    filter_status = col_f2.selectbox("Filter Status", ["All", "In Home Room", "Relocated", "Out for Repair"])

    # Apply Filters
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
        st.info("No equipment registered yet. Register your first device below.")

    st.markdown("---")

    # Form to Add or Update Equipment
    with st.expander("➕ Add / Update Equipment Asset in Register"):
        with st.form("asset_register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                asset_tag = st.text_input("Asset Tag / Serial Number *", placeholder="e.g., TITAN-126398")
                device_name = st.text_input("Device Name / Model *", placeholder="e.g., Interacoustics Titan")
                home_site = st.selectbox("Home Site *", ["CYPAC", "Community", "Mobile"])
                home_room = st.selectbox("Home Room *", room_names)
                
            with col2:
                current_status = st.selectbox("Current Operational Status", ["In Home Room", "Relocated", "Out for Repair", "Retired / Decommissioned"])
                last_cal_date = st.date_input("Last Calibration Date", datetime.date.today())
                
                # Calculate default next calibration (1 year)
                next_cal_default = last_cal_date + datetime.timedelta(days=365)
                next_cal_date = st.date_input("Next Calibration Due Date", next_cal_default)
                notes = st.text_input("Notes / Equipment Specs", placeholder="e.g., Transducer SN: 3045501")

            if st.form_submit_button("⚡ Save Asset Record", type="primary", use_container_width=True):
                if not asset_tag or not device_name:
                    st.error("Please provide both an Asset Tag/Serial No and Device Name.")
                else:
                    db.save_asset(
                        asset_tag,
                        device_name,
                        home_site,
                        home_room,
                        current_status,
                        last_cal_date.strftime("%Y-%m-%d"),
                        next_cal_date.strftime("%Y-%m-%d"),
                        notes
                    )
                    st.success(f"✅ Saved asset **{device_name} ({asset_tag})** assigned to **{home_room}**!")
