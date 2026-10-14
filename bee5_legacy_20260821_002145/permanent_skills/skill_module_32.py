import sqlite3

class Bee5:
    def __init__(self):
        self.conn = sqlite3.connect('shared_memory.db')
        self.cursor = self.conn.cursor()

    def execute_query(self, query):
        self.cursor.execute(query)
        self.conn.commit()

    def close_connection(self):
        self.conn.close()

bee5 = Bee5()
query = "CREATE TABLE IF NOT EXISTS skills (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
bee5.execute_query(query)
bee5.close_connection()