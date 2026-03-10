import sqlite3

DB = "water_system.db"


def create_tables():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # -----------------------------
    # RAW SENSOR DATA
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS sensor_readings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        apt_id TEXT,

        timestamp TEXT,

        flow_rate_lpm REAL,

        volume_l REAL,

        duration_s INTEGER,

        tank_pct REAL,

        wifi_rssi INTEGER,

        hour_of_day INTEGER,

        is_anomaly INTEGER DEFAULT 0,

        anomaly_score REAL DEFAULT 0

    )

    """)

    # index for faster ML queries
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_timestamp
    ON sensor_readings(timestamp)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_apartment
    ON sensor_readings(apt_id)
    """)


    # -----------------------------
    # PROCESSED DATA TABLE
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS processed_readings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        apt_id TEXT,

        timestamp TEXT,

        flow_rate_lpm REAL,

        volume_l REAL,

        duration_s INTEGER,

        tank_pct REAL,

        wifi_rssi INTEGER,

        rolling_mean_5 REAL,

        rolling_std_5 REAL,

        spike_flag INTEGER DEFAULT 0

    )

    """)


    # -----------------------------
    # ALERT LOG TABLE
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS alerts(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        apt_id TEXT,

        timestamp TEXT,

        flow_rate REAL,

        duration INTEGER,

        anomaly_score REAL,

        alert_type TEXT

    )

    """)


    # -----------------------------
    # TANK HISTORY TABLE
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS tank_readings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        timestamp TEXT,

        tank_pct REAL

    )

    """)


    conn.commit()
    conn.close()

    print("Database schema initialized successfully")


if __name__ == "__main__":

    create_tables()