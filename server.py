from flask import Flask, jsonify
import sqlite3

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
# HOME
# -----------------------------
@app.route("/")
def home():

    return {
        "message": "AquaGuard Server Running",
        "dashboard": "/dashboard",
        "data_api": "/data",
        "alerts_api": "/alerts",
        "tank_api": "/tank",
        "export_api": "/export"
    }


# -----------------------------
# DATA API FOR GRAPH
# -----------------------------
@app.route("/data")
def get_data():

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT
            timestamp,
            apt_id,
            flow_rate_lpm,
            duration_s,
            tank_pct,
            is_anomaly
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 50
    """).fetchall()

    conn.close()

    data = []

    for r in rows:
        data.append({
            "timestamp": r["timestamp"],
            "apartment": r["apt_id"],
            "flow": r["flow_rate_lpm"],
            "duration": r["duration_s"],
            "tank": r["tank_pct"],
            "anomaly": r["is_anomaly"]
        })

    return jsonify(data)


# -----------------------------
# ALERTS API
# -----------------------------
@app.route("/alerts")
def get_alerts():

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT
            apt_id,
            timestamp,
            flow_rate,
            duration,
            anomaly_score,
            alert_type
        FROM alerts
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    alerts = []

    for r in rows:
        alerts.append({
            "apartment": r["apt_id"],
            "time": r["timestamp"],
            "flow": r["flow_rate"],
            "duration": r["duration"],
            "score": r["anomaly_score"],
            "type": r["alert_type"]
        })

    return jsonify(alerts)


# -----------------------------
# TANK LEVEL API
# -----------------------------
@app.route("/tank")
def get_tank():

    conn = get_db_connection()

    row = conn.execute("""
        SELECT tank_pct
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    conn.close()

    if row:
        return jsonify({"tank_pct": row["tank_pct"]})

    return jsonify({"tank_pct": 0})


# -----------------------------
# CSV EXPORT API
# -----------------------------
import csv
from flask import Response

@app.route("/export")
def export_csv():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT
            id, apt_id, timestamp, flow_rate_lpm, volume_l, duration_s, tank_pct, is_anomaly
        FROM sensor_readings
        ORDER BY id ASC
    """).fetchall()
    conn.close()

    def generate():
        yield 'id,apt_id,timestamp,flow_rate_lpm,volume_l,duration_s,tank_pct,is_anomaly\n'
        for row in rows:
            yield f'{row["id"]},{row["apt_id"]},{row["timestamp"]},{row["flow_rate_lpm"]},{row["volume_l"]},{row["duration_s"]},{row["tank_pct"]},{row["is_anomaly"]}\n'

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment; filename=sensor_data.csv"})


# -----------------------------
# DASHBOARD PAGE
# -----------------------------
@app.route("/dashboard")
def dashboard():

    html = """

<html>

<head>

<title>AquaGuard Water Monitoring</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

body{
font-family:Arial;
background:#f4f6f8;
padding:20px;
}

h1{
text-align:center;
}

#alert{
color:red;
font-weight:bold;
font-size:20px;
text-align:center;
margin-bottom:20px;
}

#tank{
font-size:18px;
text-align:center;
margin-bottom:20px;
}

canvas{
background:white;
border-radius:10px;
padding:20px;
}

table{
width:100%;
border-collapse:collapse;
margin-top:20px;
background:white;
}

th,td{
border:1px solid #ddd;
padding:8px;
text-align:center;
}

th{
background:#333;
color:white;
}

.alert-HIGH { background-color: #ffcccc; color: #cc0000; font-weight: bold; }
.alert-MEDIUM { background-color: #ffe5cc; color: #cc6600; font-weight: bold; }
.alert-LOW { background-color: #ffffcc; color: #cccc00; font-weight: bold; }

.btn-export {
    display: inline-block;
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 5px;
    font-weight: bold;
    margin-bottom: 20px;
}

</style>

</head>

<body>

<h1>AquaGuard Water Monitoring Dashboard</h1>

<div style="text-align:center;">
    <a href="/export" class="btn-export">Export Historical Data CSV</a>
</div>

<div id="alert"></div>

<div id="tank">Tank Level: -- %</div>

<canvas id="flowChart"></canvas>

<h2>Recent Alerts</h2>

<table id="alertTable">

<thead>
<tr>
<th>Apartment</th>
<th>Time</th>
<th>Flow</th>
<th>Duration</th>
<th>Type</th>
</tr>
</thead>

<tbody></tbody>

</table>


<script>

let ctx = document.getElementById("flowChart").getContext("2d");

let chart = new Chart(ctx,{
type:"line",
data:{
labels:[],
datasets:[{
label:"Flow Rate (LPM)",
data:[],
borderColor:"blue",
fill:false
}]
},
options:{
responsive:true,
scales:{
y:{beginAtZero:true}
}
}
});


async function updateData(){

let response = await fetch("/data");
let data = await response.json();

data.reverse();

let labels=[];
let values=[];
let alertText="";

data.forEach(d=>{

labels.push(d.timestamp);
values.push(d.flow);

if(d.anomaly==1){
alertText="⚠ LEAK DETECTED IN "+d.apartment;
}

});

chart.data.labels=labels;
chart.data.datasets[0].data=values;
chart.update();

document.getElementById("alert").innerHTML=alertText;

}


async function updateTank(){

let response = await fetch("/tank");
let data = await response.json();

document.getElementById("tank").innerHTML =
"Tank Level: "+data.tank_pct.toFixed(1)+" %";

}


async function updateAlerts(){

let response = await fetch("/alerts");
let alerts = await response.json();

let table = document.querySelector("#alertTable tbody");

table.innerHTML="";

alerts.forEach(a=>{

// Determine CSS class based on alert_type
let rowClass = "";
if (a.type && a.type.includes("HIGH")) {
    rowClass = "alert-HIGH";
} else if (a.type && a.type.includes("MEDIUM")) {
    rowClass = "alert-MEDIUM";
} else if (a.type && a.type.includes("LOW")) {
    rowClass = "alert-LOW";
}

let row="<tr class='"+rowClass+"'>"+
"<td>"+a.apartment+"</td>"+
"<td>"+a.time+"</td>"+
"<td>"+a.flow+"</td>"+
"<td>"+a.duration+"</td>"+
"<td>"+a.type+"</td>"+
"</tr>";

table.innerHTML+=row;

});

}


function refresh(){

updateData();
updateTank();
updateAlerts();

}

setInterval(refresh,3000);

refresh();

</script>

</body>

</html>

"""

    return html


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)