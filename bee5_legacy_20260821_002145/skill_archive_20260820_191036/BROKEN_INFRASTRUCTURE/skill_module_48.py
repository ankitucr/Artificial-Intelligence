import sqlite3
import time

def create_connection():
    return sqlite3.connect('shared_memory.db')

def execute_query(query):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()

def main():
    query = "SELECT * FROM main"
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        print(result)
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")