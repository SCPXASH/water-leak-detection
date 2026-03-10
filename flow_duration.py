import sqlite3
import time

DB = "water_system.db"

FLOW_THRESHOLD = 0.1   # LPM


def update_duration():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # Get last two readings
    rows = cursor.execute("""
        SELECT id, flow_rate_lpm, duration_s
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 2
    """).fetchall()

    if len(rows) < 2:
        conn.close()
        return

    current = rows[0]
    previous = rows[1]

    current_id = current[0]
    flow_rate = current[1]
    prev_duration = previous[2]

    if flow_rate > FLOW_THRESHOLD:
        new_duration = prev_duration + 10
    else:
        new_duration = 0

    cursor.execute("""
        UPDATE sensor_readings
        SET duration_s = ?
        WHERE id = ?
    """, (new_duration, current_id))

    conn.commit()
    conn.close()

    print("Duration updated:", new_duration)


if __name__ == "__main__":

    print("Flow Duration Tracker Running...")

    while True:
        update_duration()
        time.sleep(10)