import sqlite3
import datetime
import random
import time

DB = "water_system.db"

def simulate_leak():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    print("Starting leak simulation...\n")

    for i in range(20):

        timestamp = datetime.datetime.now()

        flow_rate = random.uniform(7,10)   # high flow
        volume = random.uniform(50,120)
        duration = random.randint(1500,2500)  # long duration
        tank = random.uniform(40,70)
        wifi = random.randint(-85,-60)
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

        print(f"Leak data inserted: flow={flow_rate:.2f} LPM duration={duration}")

        time.sleep(1)

    conn.close()

    print("\nLeak simulation complete.")


if __name__ == "__main__":

    simulate_leak()