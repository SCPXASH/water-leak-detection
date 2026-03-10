import sqlite3
import pandas as pd
import time

DB = "water_system.db"


# -----------------------------
# CREATE PROCESSED TABLE
# -----------------------------
def init_processed_table():

    conn = sqlite3.connect(DB)

    conn.execute("""

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

    conn.commit()
    conn.close()


# -----------------------------
# LOAD RAW DATA
# -----------------------------
def load_data():

    conn = sqlite3.connect(DB)

    df = pd.read_sql_query("""

    SELECT *
    FROM sensor_readings
    ORDER BY id DESC
    LIMIT 100

    """, conn)

    conn.close()

    return df


# -----------------------------
# CLEAN DATA
# -----------------------------
def clean_data(df):

    # Remove impossible flow values
    df.loc[df["flow_rate_lpm"] > 30, "flow_rate_lpm"] = 0

    # Fill missing values
    df.fillna(0, inplace=True)

    return df


# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def add_features(df):

    df = df.sort_values("timestamp")

    df["rolling_mean_5"] = (
        df["flow_rate_lpm"]
        .rolling(5, min_periods=1)
        .mean()
    )

    df["rolling_std_5"] = (
        df["flow_rate_lpm"]
        .rolling(5, min_periods=1)
        .std()
        .fillna(0)
    )

    # spike detection
    df["spike_flag"] = (
        df["flow_rate_lpm"] > df["rolling_mean_5"] * 3
    ).astype(int)

    return df


# -----------------------------
# SAVE PROCESSED DATA
# -----------------------------
def save_processed(df):

    conn = sqlite3.connect(DB)

    for _, row in df.iterrows():

        conn.execute("""

        INSERT INTO processed_readings(

            apt_id,
            timestamp,
            flow_rate_lpm,
            volume_l,
            duration_s,
            tank_pct,
            wifi_rssi,
            rolling_mean_5,
            rolling_std_5,
            spike_flag

        )

        VALUES (?,?,?,?,?,?,?,?,?,?)

        """, (

            row["apt_id"],
            row["timestamp"],
            row["flow_rate_lpm"],
            row["volume_l"],
            row["duration_s"],
            row["tank_pct"],
            row["wifi_rssi"],
            row["rolling_mean_5"],
            row["rolling_std_5"],
            row["spike_flag"]

        ))

    conn.commit()
    conn.close()


# -----------------------------
# PIPELINE RUNNER
# -----------------------------
def run_pipeline():

    df = load_data()

    if len(df) == 0:
        return

    df = clean_data(df)

    df = add_features(df)

    save_processed(df)

    print("Pipeline processed", len(df), "records")


# -----------------------------
# MAIN LOOP
# -----------------------------
if __name__ == "__main__":

    print("Backend Data Pipeline Running...")

    init_processed_table()

    while True:

        run_pipeline()

        time.sleep(15)