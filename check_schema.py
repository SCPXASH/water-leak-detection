import sqlite3

def check_schema():
    conn = sqlite3.connect('water_system.db')
    cursor = conn.cursor()
    cols = [col[1] for col in cursor.execute('PRAGMA table_info(sensor_readings)').fetchall()]
    print('Sensor readings schema:', cols)
    conn.close()

check_schema()
