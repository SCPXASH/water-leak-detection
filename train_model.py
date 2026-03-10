import sqlite3
import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DB = "water_system.db"


# -----------------------------
# LOAD DATA FROM DATABASE
# -----------------------------
def load_data():

    conn = sqlite3.connect(DB)

    df = pd.read_sql_query("""
        SELECT
            apt_id,
            timestamp,
            flow_rate_lpm,
            volume_l,
            duration_s,
            tank_pct,
            wifi_rssi
        FROM sensor_readings
        ORDER BY timestamp
    """, conn)

    conn.close()

    return df


# -----------------------------
# DATA CLEANING
# -----------------------------
def clean_data(df):

    # Remove impossible values
    df.loc[df["flow_rate_lpm"] > 30, "flow_rate_lpm"] = 0

    # Replace missing values
    df.fillna(0, inplace=True)

    return df


# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def build_features(df):

    df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed")

    # Time features
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    # Cyclical encoding
    df["time_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["time_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    # Sort for rolling stats
    df = df.sort_values(["apt_id", "timestamp"])

    # Rolling statistics
    df["rolling_mean_5"] = (
        df.groupby("apt_id")["flow_rate_lpm"]
        .rolling(5, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["rolling_std_5"] = (
        df.groupby("apt_id")["flow_rate_lpm"]
        .rolling(5, min_periods=1)
        .std()
        .fillna(0)
        .reset_index(level=0, drop=True)
    )

    # Spike detection
    df["spike_flag"] = (
        df["flow_rate_lpm"] > df["rolling_mean_5"] * 3
    ).astype(int)

    return df


# -----------------------------
# TRAIN MODEL
# -----------------------------
def train_model(df):

    FEATURES = [
        "flow_rate_lpm",
        "volume_l",
        "duration_s",
        "tank_pct",
        "wifi_rssi",
        "rolling_mean_5",
        "rolling_std_5",
        "spike_flag",
        "time_sin",
        "time_cos",
        "day_of_week"
    ]

    X = df[FEATURES].values

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.02,
        random_state=42
    )

    model.fit(X_scaled)

    joblib.dump(model, "leak_model.pkl")
    joblib.dump(scaler, "scaler.pkl")

    print("Model training complete")
    print("Files created:")
    print(" - leak_model.pkl")
    print(" - scaler.pkl")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    print("Loading data...")

    df = load_data()

    if len(df) < 20:
        print("Not enough data yet. Let system collect more readings.")
        exit()

    print("Cleaning data...")

    df = clean_data(df)

    print("Building features...")

    df = build_features(df)

    print("Training Isolation Forest model...")

    train_model(df)