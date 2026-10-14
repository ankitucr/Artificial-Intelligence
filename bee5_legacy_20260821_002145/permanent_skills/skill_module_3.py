import sqlite3
import time

def initialize_connection():
    return sqlite3.connect('shared_memory.db', timeout=30)

def execute_query(query):
    connection = initialize_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        connection.close()

def fetch_data(table_name):
    query = f"SELECT * FROM {table_name}"
    return execute_query(query)

def insert_data(table_name, data):
    query = f"INSERT INTO {table_name} VALUES ({', '.join('?' * len(data))})"
    return execute_query(query)

def optimize_connection():
    connection = initialize_connection()
    connection.execute('PRAGMA synchronous = OFF')
    connection.execute('PRAGMA journal_mode = MEMORY')
    connection.close()

optimize_connection()