================================================================================
  AQUAGUARD — SMART WATER LEAK DETECTION SYSTEM
  README & Developer Documentation
================================================================================

  Version   : 1.0
  Platform  : ESP32 + Python + Flask
  Database  : SQLite
  Protocol  : MQTT (Mosquitto)

--------------------------------------------------------------------------------

TABLE OF CONTENTS

  1.  Project Overview
  2.  System Architecture
  3.  Hardware Requirements
  4.  Circuit Wiring Guide
  5.  Software Requirements
  6.  Python Dependencies
  7.  Project Folder Structure
  8.  Setup & Running the System
  9.  Viewing Output & Dashboard
  10. Running a Leak Simulation
  11. Key Features
  12. Troubleshooting
  13. Authors & Technologies

================================================================================
  1. PROJECT OVERVIEW
================================================================================

AquaGuard is an IoT-based water monitoring and leak detection system designed
to continuously track water flow and identify abnormal usage patterns that may
indicate a water leak.

The system integrates the following components:

  - ESP32 sensors        : Real-time water flow and level monitoring
  - MQTT (Mosquitto)     : Lightweight IoT data transport protocol
  - SQLite database      : Local persistent storage for sensor readings
  - Machine Learning     : Anomaly detection engine (Isolation Forest)
  - Rule-based logic     : Guaranteed detection via threshold rules
  - Flask dashboard      : Live browser-based visualization and alerting

================================================================================
  2. SYSTEM ARCHITECTURE
================================================================================

  [ ESP32 Sensors ]
         |
         v
  [ MQTT Broker — Mosquitto ]
         |
         v
  [ mqtt_receiver.py ]        <-- Data ingestion layer
         |
         v
  [ SQLite Database ]         <-- water_system.db
         |
         v
  [ data_pipeline.py ]        <-- Feature engineering
         |
         v
  [ ML Leak Detection Engine ] + [ Rule-Based Logic ]
         |
         v
  [ Alerts Table ]
         |
         v
  [ Flask Dashboard ]         <-- http://localhost:5001

================================================================================
  3. HARDWARE REQUIREMENTS
================================================================================

  Component                             Quantity
  ------------------------------------  --------
  ESP32 Development Board               1
  Water Flow Sensor (YF-S201 or equiv.) 1
  Ultrasonic Sensor (HC-SR04)           1
  Resistor — 1 kΩ                       1
  Resistor — 2 kΩ                       1
  Breadboard                            1
  Jumper Wires                          Several

================================================================================
  4. CIRCUIT WIRING GUIDE
================================================================================

  ── 4.1 FLOW SENSOR WIRING ──────────────────────────────────────────────────

  Flow Sensor Pin      ESP32 Pin
  -------------------  ---------
  Red   (VCC)          5V / VIN
  Black (GND)          GND
  Yellow (Signal)      GPIO 27

  ── 4.2 ULTRASONIC SENSOR WIRING (HC-SR04) ──────────────────────────────────

  HC-SR04 Pin          ESP32 Pin
  -------------------  -------------------------
  VCC                  5V / VIN
  GND                  GND
  TRIG                 GPIO 5
  ECHO                 GPIO 18  (via voltage divider — see below)

  ── 4.3 VOLTAGE DIVIDER — ECHO PIN ──────────────────────────────────────────

  IMPORTANT: The HC-SR04 ECHO pin outputs 5V. The ESP32 GPIO maximum input is
  3.3V. A voltage divider MUST be used to avoid damaging the ESP32.

  Wiring:

    HC-SR04 ECHO
         |
        1kΩ
         |
         +--------> ESP32 GPIO 18
         |
        2kΩ
         |
        GND

  This divides the voltage from 5V down to approximately 3.3V (safe for ESP32).

  ── 4.4 FULL CONNECTION DIAGRAM ─────────────────────────────────────────────

    +-------------------------------+
    |           ESP32               |
    |                               |
    |  GPIO 27  <-- Flow Sensor Signal (Yellow)
    |  GPIO 5   --> Ultrasonic TRIG
    |  GPIO 18  <-- Ultrasonic ECHO (via voltage divider)
    |                               |
    |  5V / VIN --> Flow Sensor VCC (Red)
    |  5V / VIN --> Ultrasonic VCC
    |                               |
    |  GND      --> Flow Sensor GND (Black)
    |  GND      --> Ultrasonic GND
    +-------------------------------+

    Water Pipe:
      |
      +--> [ Flow Sensor (YF-S201) ]

    Above Water Tank:
      +--> [ HC-SR04 Ultrasonic Sensor ]
               ↓
          (measures tank level)

================================================================================
  5. SOFTWARE REQUIREMENTS
================================================================================

  ── 5.1 PYTHON ──────────────────────────────────────────────────────────────

  Requires: Python 3.10 or later
  Download: https://www.python.org/downloads/

  During installation, ensure the following option is checked:
    [x] Add Python to PATH

  Verify installation:
    > python --version

  ── 5.2 MOSQUITTO MQTT BROKER ───────────────────────────────────────────────

  Download: https://mosquitto.org/download/
  Install:  Windows Installer (64-bit)

  During installation, ensure both options are checked:
    [x] Mosquitto Broker
    [x] Mosquitto Client Utilities

  Verify installation:
    > mosquitto -v

  ── 5.3 VISUAL STUDIO CODE (RECOMMENDED) ────────────────────────────────────

  Download: https://code.visualstudio.com/

  Recommended extensions:
    - Python
    - SQLite Viewer

================================================================================
  6. PYTHON DEPENDENCIES
================================================================================

  Install all required libraries with a single command:

    > pip install pandas numpy flask scikit-learn joblib paho-mqtt

  Library breakdown:
    pandas         — Data manipulation and pipeline processing
    numpy          — Numerical operations
    flask          — Web dashboard server
    scikit-learn   — Machine learning (Isolation Forest anomaly detection)
    joblib         — Model serialization (.pkl files)
    paho-mqtt      — MQTT client for receiving ESP32 messages

================================================================================
  7. PROJECT FOLDER STRUCTURE
================================================================================

  AquaGuard/
  |
  |-- dashboard.py               # Flask web server & visualization
  |-- mqtt_receiver.py           # MQTT data ingestion from ESP32
  |-- leak_detection_engine.py   # ML + rule-based leak detection logic
  |-- simulate_leak.py           # Demo script to simulate leak events
  |-- database_setup.py          # Initializes SQLite database schema
  |-- train_model.py             # Trains and saves the ML anomaly model
  |-- data_pipeline.py           # Feature engineering from raw sensor data
  |-- alert_system.py            # Writes alerts to database
  |-- index.html                 # Dashboard front-end template
  |
  |-- leak_model.pkl             # Trained ML model (generated by train_model.py)
  |-- scaler.pkl                 # Feature scaler (generated by train_model.py)
  |-- water_system.db            # SQLite database (generated by database_setup.py)
  |
  `-- README.txt                 # This file

================================================================================
  8. SETUP & RUNNING THE SYSTEM
================================================================================

  Run each step in order. Each step should remain running in its own terminal
  unless otherwise indicated.

  ── BEFORE YOU START ────────────────────────────────────────────────────────

  For a clean run, delete the following files if they exist from a previous
  session:

    water_system.db
    leak_model.pkl
    scaler.pkl

  ── STEP 1 — Create the Database ────────────────────────────────────────────

    > python database_setup.py

  Creates:  water_system.db
  Purpose:  Initializes all required tables (sensor_data, alerts).

  ── STEP 2 — Start the MQTT Broker ──────────────────────────────────────────

    > mosquitto -v

  Leave this terminal running.

  Expected output:
    Opening ipv4 listen socket on port 1883

  ── STEP 3 — Start the MQTT Receiver ────────────────────────────────────────

    > python mqtt_receiver.py

  Leave this terminal running.

  Expected output:
    MQTT Receiver Running
    Message received
    Data stored

  This process listens for incoming ESP32 sensor data over MQTT and writes
  it to the SQLite database.

  ── STEP 4 — Train the ML Model ─────────────────────────────────────────────

    > python train_model.py

  Creates:  leak_model.pkl
            scaler.pkl

  This step trains the anomaly detection model on the collected sensor data.
  Run this only after sufficient data has been collected (Step 3 running).

  ── STEP 5 — Start Leak Detection ───────────────────────────────────────────

    > python leak_detection_engine.py

  Leave this terminal running.

  Expected output:
    Leak Detection Engine Running
    Leak detection cycle completed

  This runs continuous analysis on incoming data using both ML-based anomaly
  detection and rule-based threshold checks.

  ── STEP 6 — Start the Dashboard ────────────────────────────────────────────

    > python dashboard.py

  Then open a browser and navigate to:

    http://localhost:5001

================================================================================
  9. VIEWING OUTPUT & DASHBOARD
================================================================================

  ── LIVE GRAPH ──────────────────────────────────────────────────────────────

    URL: http://localhost:5001

  Displays a real-time graph of water flow readings over time.

  ── TABLE VIEW ──────────────────────────────────────────────────────────────

    URL: http://localhost:5001/dashboard

  Shows the latest sensor readings in tabular format. Example output:

    flow_rate_lpm  |  duration_s  |  is_anomaly
    ---------------+--------------+------------
    8.5            |  2000        |  1

  Note: is_anomaly = 1 indicates a detected leak.

  ── ALERTS TABLE ────────────────────────────────────────────────────────────

  Alerts are also recorded directly in the SQLite database under the table
  named "alerts". Example record:

    apt_id   |  flow_rate  |  duration  |  alert_type
    ---------+-------------+------------+------------
    APT_101  |  8.5        |  2000      |  HIGH

================================================================================
  10. RUNNING A LEAK SIMULATION
================================================================================

  To test the system without physical hardware, run the simulation script:

    > python simulate_leak.py

  This inserts pre-defined abnormal sensor readings into the database to
  trigger the detection pipeline.

  Simulated data values:
    flow_rate_lpm = 8.5
    duration_s    = 2000

  ── EXPECTED RESULTS ────────────────────────────────────────────────────────

  1. The dashboard graph shows a visible flow spike.
  2. The table view updates to show:   is_anomaly = 1
  3. An alert record is created in the alerts table:

     flow_rate_lpm  |  duration_s  |  is_anomaly
     ---------------+--------------+------------
     8.5            |  2000        |  1

  This confirms the system is correctly detecting:   WATER LEAK DETECTED

================================================================================
  11. KEY FEATURES
================================================================================

  - Real-time IoT water flow monitoring via ESP32 sensors
  - MQTT-based communication (lightweight, reliable)
  - SQLite local storage (no external database required)
  - Machine learning anomaly detection (Isolation Forest algorithm)
  - Rule-based safety logic for guaranteed threshold detection
  - Live browser dashboard with flow graph and data table
  - Alert logging with apartment ID and severity level

================================================================================
  12. TROUBLESHOOTING
================================================================================

  ISSUE           : Dashboard not updating
  SOLUTION        : Restart the dashboard server.
                    > python dashboard.py

  ─────────────────────────────────────────────────────────────────────────────

  ISSUE           : MQTT connection error
  SOLUTION        : Ensure Mosquitto is running.
                    > mosquitto -v
                    If it was stopped, restart it and then restart mqtt_receiver.py.

  ─────────────────────────────────────────────────────────────────────────────

  ISSUE           : ML model file not found (leak_model.pkl missing)
  SOLUTION        : Re-run the training step.
                    > python train_model.py

  ─────────────────────────────────────────────────────────────────────────────

  ISSUE           : Database file not found (water_system.db missing)
  SOLUTION        : Re-run the database setup.
                    > python database_setup.py

  ─────────────────────────────────────────────────────────────────────────────

  ISSUE           : No data appearing after startup
  SOLUTION        : Confirm Steps 2 and 3 are both running (MQTT broker and
                    receiver). If using real hardware, verify ESP32 is powered
                    and connected to the same network. Use simulate_leak.py
                    to test without hardware.

================================================================================
  13. AUTHORS & TECHNOLOGIES
================================================================================

  Project   : AquaGuard — Smart Water Leak Detection System
  Type      : IoT Mini Project

  Technologies used:

    Language     : Python 3.10+
    Hardware     : ESP32, YF-S201 Flow Sensor, HC-SR04 Ultrasonic Sensor
    Protocol     : MQTT (Eclipse Mosquitto)
    Database     : SQLite
    ML Framework : scikit-learn (Isolation Forest)
    Web Server   : Flask
    Frontend     : HTML / JavaScript (Chart.js)

================================================================================
  END OF README
================================================================================
