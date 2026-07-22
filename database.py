import os
import pandas as pd

# Define the path to your system workbook
EXCEL_FILE = "CYPAC_HUMB_2026_Full_System.xlsx"

def init_db():
    """Ensure the necessary sheets and file structure exist for the application."""
    if not os.path.exists(EXCEL_FILE):
        # Create a blank workbook with required sheets if it doesn't exist
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
            pd.DataFrame(columns=["Date", "Room", "Equipment", "Result", "Technician", "Notes"]).to_excel(writer, sheet_name="DailyCalibrationLog", index=False)
            pd.DataFrame(columns=["Date", "Batch ID", "Auditor", "Compliance Status", "Resolution"]).to_excel(writer, sheet_name="ProcessAuditLog", index=False)
            pd.DataFrame(columns=["Audiologist", "Room", "Date Fault Found", "Equipment", "Serial Number", "Fault", "Internal Repair", "Repair Status", "Date Resolved"]).to_excel(writer, sheet_name="RepairLog", index=False)
    print("Database/Workbook initialized successfully.")

def load_calibration_data():
    """Load the daily calibration log into a Pandas DataFrame."""
    if os.path.exists(EXCEL_FILE):
        try:
            return pd.read_excel(EXCEL_FILE, sheet_name="DailyCalibrationLog")
        except Exception:
            return pd.DataFrame(columns=["Date", "Room", "Equipment", "Result", "Technician", "Notes"])
    return pd.DataFrame(columns=["Date", "Room", "Equipment", "Result", "Technician", "Notes"])

def save_calibration_data(df):
    """Save the updated calibration DataFrame back to the Excel file."""
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name="DailyCalibrationLog", index=False)

def load_audit_data():
    """Load the process audit log into a Pandas DataFrame."""
    if os.path.exists(EXCEL_FILE):
        try:
            return pd.read_excel(EXCEL_FILE, sheet_name="ProcessAuditLog")
        except Exception:
            return pd.DataFrame(columns=["Date", "Batch ID", "Auditor", "Compliance Status", "Resolution"])
    return pd.DataFrame(columns=["Date", "Batch ID", "Auditor", "Compliance Status", "Resolution"])

def save_audit_data(df):
    """Save the updated audit DataFrame back to the Excel file."""
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name="ProcessAuditLog", index=False)

def load_repair_data():
    """Load the repair log into a Pandas DataFrame."""
    if os.path.exists(EXCEL_FILE):
        try:
            return pd.read_excel(EXCEL_FILE, sheet_name="RepairLog")
        except Exception:
            return pd.DataFrame(columns=["Audiologist", "Room", "Date Fault Found", "Equipment", "Serial Number", "Fault", "Internal Repair", "Repair Status", "Date Resolved"])
    return pd.DataFrame(columns=["Audiologist", "Room", "Date Fault Found", "Equipment", "Serial Number", "Fault", "Internal Repair", "Repair Status", "Date Resolved"])

def save_repair_data(df):
    """Save the updated repair DataFrame back to the Excel file."""
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name="RepairLog", index=False)

# Initialize the database directly when the module is loaded
init_db()
