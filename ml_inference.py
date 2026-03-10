import sqlite3
import joblib
import numpy as np
import datetime
import time

DB = "water_system.db"

MODEL_FILE = "leak_model.pkl"
SCALER_FILE = "scaler.pkl"

THRESHOLD = 0.55


# -----------------------------
# LOAD MODEL
# -----------------------------
model = joblib.load(MODEL_FILE)
scaler = joblib.load(SCALER_FILE)


# -----------------------------
# GET LATEST SENSOR DATA
# -----------------------------
def get_latest():

    conn = sqlite3.connect(DB)

    row = conn.execute("""
        SELECT id, apt_id, flow_rate_lpm, duration_s, hour_of_day
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    return row


# -----------------------------
# BUILD FEATURE VECTOR
# -----------------------------
def build_features(flow, duration, hour):

    time_sin = np.sin(2 * np.pi * hour / 24)
    time_cos = np.cos(2 * np.pi * hour / 24)

    rolling_mean = flow
    rolling_std = 0.1

    features = np.array([[
        flow,
        duration,
        rolling_mean,
        rolling_std,
        time_sin,
        time_cos,
        datetime.datetime.now().weekday()
    ]])

    return features


# -----------------------------
# RUN ML DETECTION
# -----------------------------
def detect():

    row = get_latest()

    if row is None:
        return

    record_id = row[0]
    apt_id = row[1]
    flow = row[2]
    duration = row[3]
    hour = row[4]

    features = build_features(flow, duration, hour)

    scaled = scaler.transform(features)

    score = -model.score_samples(scaled)[0]

    anomaly = 1 if score > THRESHOLD else 0

    conn = sqlite3.connect(DB)

    conn.execute("""
        UPDATE sensor_readings
        SET anomaly_score = ?, is_anomaly = ?
        WHERE id = ?
    """, (score, anomaly, record_id))

    conn.commit()
    conn.close()

    if anomaly:

        print("⚠ ML LEAK ALERT")
        print("Apartment:", apt_id)
        print("Flow:", flow)
        print("Duration:", duration)
        print("Score:", score)
        print("-------------------------")


# -----------------------------
# MAIN LOOP
# -----------------------------
if __name__ == "__main__":

    print("ML Leak Detection Running...")

    while True:

        detect()

        time.sleep(10)