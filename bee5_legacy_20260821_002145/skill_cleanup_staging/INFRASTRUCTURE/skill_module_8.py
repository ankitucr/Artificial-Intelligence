import sqlite3
import time

def create_connection():
    return sqlite3.connect('shared_memory.db', timeout=30)

def execute_query(query):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(e)
    finally:
        conn.close()

def main():
    query = "SELECT * FROM table_name"
    start_time = time.time()
    results = execute_query(query)
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")

if __name__ == "__main__":
    main()