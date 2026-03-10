import sqlite3
import datetime
import time
import random

DB = "water_system.db"

FLOW_THRESHOLD = 5
DURATION_THRESHOLD = 1500


def insert_leak_data():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    timestamp = datetime.datetime.now()

    flow_rate = random.uniform(7,10)     # strong flow
    volume = random.uniform(50,120)
    duration = random.randint(1800,3000) # long duration
    tank = random.uniform(40,70)
    wifi = -70
    hour = timestamp.hour

    cursor.execute("""
    INSERT INTO sensor_readings
    (apt_id,timestamp,flow_rate_lpm,volume_l,duration_s,tank_pct,wifi_rssi,hour_of_day)
    VALUES (?,?,?,?,?,?,?,?)
    """,(

    "APT_101",
    timestamp,
    flow_rate,
    volume,
    duration,
    tank,
    wifi,
    hour

    ))

    conn.commit()
    conn.close()

    print("Leak-like sensor data inserted.")
    print(f"Flow: {flow_rate:.2f} LPM | Duration: {duration} seconds\n")


def detect_leak():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    row = cursor.execute("""
    SELECT apt_id,timestamp,flow_rate_lpm,duration_s
    FROM sensor_readings
    ORDER BY id DESC
    LIMIT 1
    """).fetchone()

    conn.close()

    if not row:
        print("No data found.")
        return

    apt_id, timestamp, flow_rate, duration = row

    print("Checking system for leaks...\n")

    time.sleep(2)

    if flow_rate > FLOW_THRESHOLD and duration > DURATION_THRESHOLD:

        print("===================================")
        print("🚨🚨🚨 WATER LEAK ALERT 🚨🚨🚨")
        print("===================================")
        print(f"Apartment: {apt_id}")
        print(f"Time: {timestamp}")
        print(f"Flow Rate: {flow_rate:.2f} LPM")
        print(f"Duration: {duration} seconds")
        print("\nSTATUS: POSITIVE FOR WATER LEAK")
        print("===================================\n")

    else:

        print("System Status: NORMAL (No Leak)\n")


if __name__ == "__main__":

    print("\n===== WATER LEAK DETECTION DEMO =====\n")

    time.sleep(1)

    insert_leak_data()

    time.sleep(2)

    detect_leak()