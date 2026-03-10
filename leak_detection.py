import sqlite3
import datetime
import time

DB = "water_system.db"

FLOW_THRESHOLD = 0.1   # LPM


def check_leak():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT id, apt_id, flow_rate_lpm, duration_s, hour_of_day
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    if not row:
        conn.close()
        return

    record_id = row[0]
    apt_id = row[1]
    flow_rate = row[2]
    duration = row[3]
    hour = row[4]

    leak_detected = False
    reason = ""

    # -----------------------------
    # RULE 1: Morning Peak (Disable)
    # -----------------------------
    if 7 <= hour < 10:
        leak_detected = False

    # -----------------------------
    # RULE 2: Daytime (10 AM – 7 PM)
    # -----------------------------
    elif 10 <= hour < 19:
        if flow_rate > FLOW_THRESHOLD and duration > 900:
            leak_detected = True
            reason = "Daytime continuous flow > 15 min"

    # -----------------------------
    # RULE 3: Evening (7 PM – 10 PM)
    # -----------------------------
    elif 19 <= hour < 22:
        if flow_rate > FLOW_THRESHOLD and duration > 1800:
            leak_detected = True
            reason = "Evening continuous flow > 30 min"

    # -----------------------------
    # RULE 4: Night (10 PM – 7 AM)
    # -----------------------------
    else:
        if flow_rate > 0.05 and duration > 900:
            leak_detected = True
            reason = "Night drip leak detected"

    # -----------------------------
    # Update Database
    # -----------------------------
    if leak_detected:

        cursor.execute("""
            UPDATE sensor_readings
            SET is_anomaly = 1
            WHERE id = ?
        """, (record_id,))

        conn.commit()

        print("⚠ LEAK DETECTED")
        print("Apartment:", apt_id)
        print("Flow Rate:", flow_rate, "LPM")
        print("Duration:", duration, "seconds")
        print("Reason:", reason)
        print("---------------------------")

    conn.close()


if __name__ == "__main__":

    print("Leak Detection Engine Running...")

    while True:
        check_leak()
        time.sleep(10)