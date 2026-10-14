import sqlite3
import time

def execute_query(query):
    conn = sqlite3.connect('shared_memory.db', timeout=5.0)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()

def get_data(query):
    conn = sqlite3.connect('shared_memory.db', timeout=5.0)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def main():
    query = "SELECT * FROM your_table"
    start_time = time.time()
    try:
        data = get_data(query)
        if time.time() - start_time > 5:
            print("Query took too long")
        else:
            print(data)
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()