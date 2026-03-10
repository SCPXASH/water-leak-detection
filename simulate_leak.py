import sqlite3
import datetime

conn = sqlite3.connect("water_system.db")
cursor = conn.cursor()

for i in range(20):

    cursor.execute("""
    INSERT INTO sensor_readings
    (apt_id,timestamp,flow_rate_lpm,volume_l,duration_s,tank_pct,wifi_rssi,hour_of_day,is_anomaly,anomaly_score)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    """,(

    "APT_101",
    datetime.datetime.now(),
    8.5,      # high flow
    120,
    2000,     # long duration
    60,
    -70,
    datetime.datetime.now().hour,
    1,        # force anomaly detection
    0.95      # high anomaly score

    ))

conn.commit()
conn.close()

print("Leak simulation data inserted with POSITIVE anomaly detection!")