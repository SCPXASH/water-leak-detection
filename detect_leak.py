import joblib
import sqlite3
import numpy as np
import time

model = joblib.load("leak_model.pkl")
scaler = joblib.load("scaler.pkl")

DB="water_system.db"

def get_latest():

    conn=sqlite3.connect(DB)

    row=conn.execute("""
    SELECT flow_rate
    FROM sensor_readings
    ORDER BY timestamp DESC
    LIMIT 1
    """).fetchone()

    conn.close()

    return row

def detect():

    row=get_latest()

    if row is None:
        return

    flow=row[0]

    features=np.array([[flow,0.1,flow]])

    scaled=scaler.transform(features)

    score=-model.score_samples(scaled)[0]

    if score>0.55:

        print("🚨 LEAK DETECTED")

    else:

        print("Normal")

while True:

    detect()

    time.sleep(10)