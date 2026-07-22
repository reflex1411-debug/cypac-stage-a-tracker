import datetime
import os
import sqlite3
import pandas as pd


class CalibrationDatabase:

    def __init__(self, db_path="cypac_stage_a.db"):
        """Initializes SQLite database connection and creates required tables if missing."""
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        """Returns a standard SQLite connection object."""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Creates tables for Stage A checks, asset inventory, fault lifecycles, and audit logs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Stage A Daily Checks Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stage_a_checks (
                    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_date TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    equipment_id TEXT NOT NULL,
                    clinician_name TEXT NOT NULL,
                    visual_inspection TEXT,
                    listening_check TEXT,
                    calibration_status TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 2. Asset Register / Clinic Rooms Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    equipment_type TEXT NOT NULL,
                    model TEXT,
                    serial_number TEXT,
                    annual_cal_due_date TEXT,
                    status TEXT DEFAULT 'Active'
                )
            """
            )

            # 3. Fault Lifecycle Tracker Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS faults (
                    fault_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_id INTEGER,
                    room_id TEXT NOT NULL,
                    equipment_id TEXT NOT NULL,
                    date_reported TEXT NOT NULL,
                    fault_description TEXT NOT NULL,
                    status TEXT DEFAULT 'Open',
                    date_resolved TEXT,
                    resolution_notes TEXT,
                    FOREIGN KEY (check_id) REFERENCES stage_a_checks(check_id)
                )
            """
            )

            # 4. Audit Log Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT
                )
            """
            )

            conn.commit()

    # =========================================================================
    # STAGE A DAILY CHECKS METHODS
    # =========================================================================

    def get_today_checks(self, today_str=None):
        """Fetches all Stage A checks recorded for a given date (defaults to today)

        and returns them as a Pandas DataFrame.
        """
        if today_str is None:
            today_str = datetime.date.today().strftime("%Y-%m-%d")

        query = """
            SELECT 
                check_id,
                check_date,
                room_id,
                equipment_id,
                clinician_name,
                visual_inspection,
                listening_check,
                calibration_status,
                notes,
                created_at
            FROM stage_a_checks
            WHERE check_date = ?
            ORDER BY created_at DESC
        """

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(today_str,))

        return df

    def save_stage_a_check(
        self,
        room_id,
        equipment_id,
        clinician_name,
        visual_inspection,
        listening_check,
        calibration_status,
        notes="",
        check_date=None,
    ):
        """Saves a new daily Stage A calibration check record."""
        if check_date is None:
            check_date = datetime.date.today().strftime("%Y-%m-%d")

        query = """
            INSERT INTO stage_a_checks (
                check_date, room_id, equipment_id, clinician_name, 
                visual_inspection, listening_check, calibration_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    check_date,
                    room_id,
                    equipment_id,
                    clinician_name,
                    visual_inspection,
                    listening_check,
                    calibration_status,
                    notes,
                ),
            )
            check_id = cursor.lastrowid
            conn.commit()

        # Log action to audit history
        self.log_audit(
            clinician_name,
            "STAGE_A_CHECK",
            f"Submitted check ID {check_id} for {room_id} ({calibration_status})",
        )

        return check_id

    # =========================================================================
    # FAULT & REPAIR LIFECYCLE METHODS
    # =========================================================================

    def log_fault(
        self,
        room_id,
        equipment_id,
        fault_description,
        check_id=None,
        reported_by="System",
    ):
        """Logs a new clinic room/equipment fault."""
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        query = """
            INSERT INTO faults (check_id, room_id, equipment_id, date_reported, fault_description, status)
            VALUES (?, ?, ?, ?, ?, 'Open')
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    check_id,
                    room_id,
                    equipment_id,
                    today_str,
                    fault_description,
                ),
            )
            fault_id = cursor.lastrowid
            conn.commit()

        self.log_audit(
            reported_by,
            "FAULT_REPORTED",
            f"Fault #{fault_id} logged for {room_id}: {fault_description}",
        )
        return fault_id

    def get_open_faults(self):
        """Retrieves all currently open faults as a DataFrame."""
        query = (
            "SELECT * FROM faults WHERE status = 'Open' ORDER BY date_reported"
            " DESC"
        )
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)

    def resolve_fault(self, fault_id, resolution_notes, resolved_by="Admin"):
        """Marks an open fault as resolved with resolution details."""
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        query = """
            UPDATE faults 
            SET status = 'Resolved', date_resolved = ?, resolution_notes = ?
            WHERE fault_id = ?
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (today_str, resolution_notes, fault_id))
            conn.commit()

        self.log_audit(
            resolved_by,
            "FAULT_RESOLVED",
            f"Fault #{fault_id} marked as resolved: {resolution_notes}",
        )

    # =========================================================================
    # AUDIT LOGGING & ASSET REGISTRATION
    # =========================================================================

    def log_audit(self, user, action, details):
        """Inserts a new record into the audit log."""
        query = "INSERT INTO audit_logs (user, action, details) VALUES (?, ?, ?)"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user, action, details))
            conn.commit()

    def get_all_assets(self):
        """Returns the full clinic room asset inventory."""
        query = "SELECT * FROM assets ORDER BY room_id ASC"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)


# Instantiation for direct module imports
db = CalibrationDatabase()
