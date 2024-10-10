# не робоча частина
import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            start_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_appointment(user_id, name, phone, start_time):
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO appointments (user_id, name, phone, start_time) VALUES (?, ?, ?, ?)',
                   (user_id, name, phone, start_time))
    conn.commit()
    conn.close()

def check_appointment_exists(start_time):
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE start_time = ?', (start_time,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def get_free_slots(date):
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Отримати вже зайняті прийоми на цю дату
    cursor.execute("SELECT start_time FROM appointments WHERE DATE(start_time) = ?", (date,))
    occupied_slots = [row[0] for row in cursor.fetchall()]

    free_slots = []
    available_hours = [10, 12, 14, 16, 18, 20]  # Доступні години
    appointment_duration = timedelta(hours=2)

    for hour in available_hours:
        current_time = datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=hour)
        if current_time.strftime('%Y-%m-%d %H:%M') not in occupied_slots:
            free_slots.append(current_time)

    conn.close()
    return free_slots
