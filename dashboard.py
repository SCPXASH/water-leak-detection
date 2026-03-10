from flask import Flask, jsonify, send_file
import sqlite3
import pandas as pd

app = Flask(__name__)

DB = "water_system.db"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# GRAPH DASHBOARD (index.html)
# -----------------------------
@app.route("/")
def home():
    return send_file("index.html")


# -----------------------------
# TABLE DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():

    conn = get_db_connection()

    df = pd.read_sql_query(
        "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 50",
        conn
    )

    conn.close()

    html = """
    <html>
    <head>

    <meta http-equiv="refresh" content="5">

    <title>Water Leak Detection Dashboard</title>

    <style>

    body{
        font-family: Arial;
        padding:20px;
        background:#f5f5f5;
    }

    h2{
        text-align:center;
    }

    table{
        border-collapse:collapse;
        width:100%;
        background:white;
    }

    th,td{
        border:1px solid #ddd;
        padding:10px;
        text-align:center;
    }

    th{
        background:#333;
        color:white;
    }

    </style>

    </head>

    <body>

    <h2>Water Leak Detection Dashboard (Table View)</h2>

    """ + df.to_html(index=False) + """

    </body>
    </html>
    """

    return html


# -----------------------------
# DATA API FOR CHART
# -----------------------------
@app.route("/data")
def data():

    conn = get_db_connection()

    df = pd.read_sql_query(
        """
        SELECT timestamp, flow_rate_lpm
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 50
        """,
        conn
    )

    conn.close()

    # ensure chart shows time in correct order
    df = df.sort_values("timestamp")

    return jsonify(df.to_dict(orient="records"))


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5001)