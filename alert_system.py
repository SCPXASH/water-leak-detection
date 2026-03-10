import sqlite3
import time
import os
import smtplib
from email.mime.text import MIMEText

DB = "water_system.db"

# -----------------------------
# EMAIL SETTINGS
# -----------------------------
EMAIL_SENDER = "waterleak@gmail.com"
EMAIL_PASSWORD = "rnse gcbc gkjb qign"  # Use app password for Gmail
EMAIL_RECEIVER = "waterleak@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# -----------------------------
# SEND EMAIL ALERT
# -----------------------------
def send_email_alert(message):

    try:

        msg = MIMEText(message)

        # Extract severity and set subject
        subject = "⚠ AquaGuard Leak Alert"
        if "HIGH" in message:
            subject = "🚨 CRITICAL: AquaGuard HIGH Severity Leak Alert"
        elif "MEDIUM" in message:
            subject = "⚠ WARNING: AquaGuard MEDIUM Severity Leak Alert"
        elif "LOW" in message:
            subject = "ℹ NOTICE: AquaGuard LOW Severity Leak Alert"

        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()

        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        server.quit()

        print("Email alert sent!")

    except Exception as e:
        print("Email error:", e)


# -----------------------------
# CHECK DATABASE FOR LEAK
# -----------------------------

LAST_ALERT_ID_FILE = "last_alert.txt"

def get_last_alert_id():
    if os.path.exists(LAST_ALERT_ID_FILE):
        with open(LAST_ALERT_ID_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return 0

def save_last_alert_id(last_id):
    with open(LAST_ALERT_ID_FILE, "w") as f:
        f.write(str(last_id))

def check_alert():

    last_id = get_last_alert_id()

    conn = sqlite3.connect(DB)

    # Fetch new alerts
    rows = conn.execute("""
        SELECT id, apt_id, flow_rate, duration, alert_type, timestamp
        FROM alerts
        WHERE id > ?
        ORDER BY id ASC
    """, (last_id,)).fetchall()

    conn.close()

    for row in rows:
        alert_id = row[0]
        apt = row[1]
        flow = row[2]
        duration = row[3]
        alert_type = row[4]
        timestamp = row[5]

        message = f"""
        AquaGuard Leak Alert!

        Time: {timestamp}
        Apartment: {apt}
        Severity / Reason: {alert_type}
        Flow Rate: {flow} LPM
        Duration: {duration} seconds

        Please check the dashboard for more details.
        """

        print(f"⚠ [{alert_type}] ALERT TRIGGERED For {apt}")

        send_email_alert(message)
        
        save_last_alert_id(alert_id)


# -----------------------------
# MAIN LOOP
# -----------------------------
if __name__ == "__main__":

    print("Alert System Running...")

    while True:

        check_alert()

        time.sleep(15)