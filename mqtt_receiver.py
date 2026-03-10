import paho.mqtt.client as mqtt
import sqlite3
import json
import datetime

DB = "water_system.db"


# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():

    conn = sqlite3.connect(DB)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        apt_id TEXT,

        timestamp TEXT,

        flow_rate_lpm REAL,

        volume_l REAL,

        duration_s INTEGER,

        tank_pct REAL,

        wifi_rssi INTEGER,

        hour_of_day INTEGER,

        is_anomaly INTEGER DEFAULT 0,

        anomaly_score REAL DEFAULT 0

    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# MQTT MESSAGE HANDLER
# -----------------------------
def on_message(client, userdata, msg):

    try:

        payload = msg.payload.decode()

        data = json.loads(payload)

        apt_id = data.get("apt_id")

        flow_rate = float(data.get("flow_rate_lpm", 0))

        volume = float(data.get("volume_l", 0))

        duration = int(data.get("duration_s", 0))

        tank_pct = float(data.get("tank_pct", 0))

        wifi_rssi = int(data.get("wifi_rssi", 0))

        # timestamp from ESP32
        timestamp = data.get("timestamp")

        if timestamp is None:
            timestamp = datetime.datetime.now()

        hour = datetime.datetime.now().hour

        conn = sqlite3.connect(DB)

        conn.execute("""

        INSERT INTO sensor_readings(

            apt_id,
            timestamp,
            flow_rate_lpm,
            volume_l,
            duration_s,
            tank_pct,
            wifi_rssi,
            hour_of_day

        )

        VALUES (?,?,?,?,?,?,?,?)

        """, (

            apt_id,
            timestamp,
            flow_rate,
            volume,
            duration,
            tank_pct,
            wifi_rssi,
            hour

        ))

        conn.commit()
        conn.close()

        print("Stored:", data)

    except Exception as e:

        print("Error processing message:", e)


# -----------------------------
# MQTT CONNECT
# -----------------------------
def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("Connected to MQTT Broker")

        client.subscribe("building/#")

        print("Subscribed to topic: building/#")

    else:

        print("MQTT connection failed:", rc)


# -----------------------------
# START MQTT CLIENT
# -----------------------------
init_db()

client = mqtt.Client()

client.on_connect = on_connect

client.on_message = on_message

client.connect("localhost", 1883)

print("MQTT Receiver Running... Waiting for data")

client.loop_forever()