import sqlite3
import pandas as pd
import numpy as np
import joblib
import datetime
import time

DB = "water_system.db"

MODEL_FILE = "leak_model.pkl"
SCALER_FILE = "scaler.pkl"

# -----------------------------
# LOAD MODEL
# -----------------------------
model = joblib.load(MODEL_FILE)
scaler = joblib.load(SCALER_FILE)


# -----------------------------
# LOAD DATA
# -----------------------------
def load_recent_data():

    conn = sqlite3.connect(DB)

    df = pd.read_sql_query("""
        SELECT
            id,
            apt_id,
            timestamp,
            flow_rate_lpm,
            volume_l,
            duration_s,
            tank_pct,
            wifi_rssi
        FROM sensor_readings
        ORDER BY timestamp DESC
        LIMIT 50
    """, conn)

    conn.close()

    return df


# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def build_features(df):

    # Fix for mixed timestamp formats
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="mixed",
        errors="coerce"
    )

    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    df["time_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["time_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    df = df.sort_values(["apt_id", "timestamp"])

    df["rolling_mean_5"] = (
        df.groupby("apt_id")["flow_rate_lpm"]
        .rolling(5, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["rolling_std_5"] = (
        df.groupby("apt_id")["flow_rate_lpm"]
        .rolling(5, min_periods=1)
        .std()
        .fillna(0)
        .reset_index(level=0, drop=True)
    )

    df["spike_flag"] = (
        df["flow_rate_lpm"] > df["rolling_mean_5"] * 3
    ).astype(int)

    return df


# -----------------------------
# RULE BASED DETECTION
# -----------------------------
def rule_engine(row):

    flow = row["flow_rate_lpm"]
    duration = row["duration_s"]

    # DEMO RULE (guaranteed leak detection)
    if flow > 5 and duration > 1200:
        return True, "High flow for long duration"

    return False, None


# -----------------------------
# ML DETECTION
# -----------------------------
def ml_detection(df):

    FEATURES = [
        "flow_rate_lpm",
        "volume_l",
        "duration_s",
        "tank_pct",
        "wifi_rssi",
        "rolling_mean_5",
        "rolling_std_5",
        "spike_flag",
        "time_sin",
        "time_cos",
        "day_of_week"
    ]

    try:

        X = df[FEATURES].values
        X_scaled = scaler.transform(X)

        scores = -model.score_samples(X_scaled)

    except Exception as e:

        print("Model error:", e)
        scores = np.zeros(len(df))

    df["anomaly_score"] = scores

    # ML anomaly threshold
    df["ml_anomaly"] = (scores > 0.35).astype(int)

    return df


# -----------------------------
# UPDATE DATABASE
# -----------------------------
def update_database(df):

    conn = sqlite3.connect(DB)

    for _, row in df.iterrows():

        rule_alert, rule_reason = rule_engine(row)
        ml_alert = row["ml_anomaly"] == 1

        severity = None
        reasons = []

        if rule_alert and ml_alert:
            severity = "HIGH"
            reasons.append("ML + Rule")
            reasons.append(rule_reason)

        elif rule_alert:
            severity = "HIGH"
            reasons.append(rule_reason)

        elif ml_alert:
            severity = "LOW"
            reasons.append("ML anomaly")

        anomaly_flag = 1 if severity else 0

        conn.execute("""
        UPDATE sensor_readings
        SET anomaly_score=?, is_anomaly=?
        WHERE id=?
        """,(
            float(row["anomaly_score"]),
            anomaly_flag,
            int(row["id"])
        ))

        if severity:

            conn.execute("""
            INSERT INTO alerts(
                apt_id,
                timestamp,
                flow_rate,
                duration,
                anomaly_score,
                alert_type
            )
            VALUES (?,?,?,?,?,?)
            """,(

                row["apt_id"],
                str(datetime.datetime.now()),
                row["flow_rate_lpm"],
                row["duration_s"],
                float(row["anomaly_score"]),
                severity + " | " + ", ".join(reasons)

            ))

    conn.commit()
    conn.close()


# -----------------------------
# MAIN DETECTION LOOP
# -----------------------------
def run_detection():

    df = load_recent_data()

    if len(df) < 5:
        return

    df = build_features(df)

    df = ml_detection(df)

    update_database(df)

    print("Leak detection cycle completed")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    print("Leak Detection Engine Running...")

    while True:

        run_detection()

        time.sleep(10)