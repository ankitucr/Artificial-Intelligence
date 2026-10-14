import sqlite3
import time

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bee5
                 (data text)''')
    conn.commit()
    conn.close()

def save_data(data):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO bee5 VALUES (?)", (data,))
    conn.commit()
    conn.close()

def read_data():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM bee5")
    rows = c.fetchall()
    conn.close()
    return rows

def main():
    create_table()
    data = "Initialization Complete"
    save_data(data)
    rows = read_data()
    for row in rows:
        print(row)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Execution Time: {time.time() - start_time} seconds")