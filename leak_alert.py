import sqlite3
import time

DB = "water_system.db"

FLOW_THRESHOLD = 5        # high flow
DURATION_THRESHOLD = 1500 # long duration


def check_for_leak():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT apt_id, timestamp, flow_rate_lpm, duration_s
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 1
    """).fetchall()

    conn.close()

    if not rows:
        return

    apt_id, timestamp, flow_rate, duration = rows[0]

    if flow_rate > FLOW_THRESHOLD and duration > DURATION_THRESHOLD:

        print("\n🚨🚨🚨 LEAK ALERT 🚨🚨🚨")
        print(f"Apartment: {apt_id}")
        print(f"Time: {timestamp}")
        print(f"Flow Rate: {flow_rate} LPM")
        print(f"Duration: {duration} seconds")
        print("Status: POSITIVE FOR LEAK\n")

    else:

        print("System Status: Normal (No Leak Detected)")


if __name__ == "__main__":

    print("Leak Alert System Started...\n")

    while True:

        check_for_leak()

        time.sleep(5)