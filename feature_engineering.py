import sqlite3
import pandas as pd
import numpy as np
import time

DB = "water_system.db"


# -----------------------------
# LOAD RAW DATA
# -----------------------------
def load_data():

    conn = sqlite3.connect(DB)

    df = pd.read_sql_query("""

    SELECT
        apt_id,
        timestamp,
        flow_rate_lpm,
        volume_l,
        duration_s,
        tank_pct,
        wifi_rssi

    FROM sensor_readings
    ORDER BY timestamp

    """, conn)

    conn.close()

    return df


# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def create_features(df):

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Hour of day
    df["hour"] = df["timestamp"].dt.hour

    # Day of week
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    # Cyclical time encoding
    df["time_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["time_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    # Rolling statistics
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

    # Spike detection
    df["spike_flag"] = (
        df["flow_rate_lpm"] > df["rolling_mean_5"] * 3
    ).astype(int)

    return df


# -----------------------------
# SAVE FEATURES
# -----------------------------
def save_features(df):

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
# PIPELINE
# -----------------------------
def run_feature_pipeline():

    df = load_data()

    if len(df) == 0:
        return

    df = create_features(df)

    save_features(df)

    print("Feature engineering completed for", len(df), "records")


# -----------------------------
# MAIN LOOP
# -----------------------------
if __name__ == "__main__":

    print("Feature Engineering Service Running...")

    while True:

        run_feature_pipeline()

        time.sleep(20)