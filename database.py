import sqlite3

def create_db():
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            dob DATE,
            gender TEXT,
            location_lat REAL,
            location_lon REAL,
            pictures TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()
