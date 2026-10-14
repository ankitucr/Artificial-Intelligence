import sqlite3
import json

def create_table(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                name text PRIMARY KEY,
                data text
                )""")
    conn.commit()

def insert_new_skill(conn, skill_name, skill_data):
    create_table(conn)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO skills (name, data) VALUES (?,?)", (skill_name, json.dumps(skill_data)))
    conn.commit()

def main():
    conn = sqlite3.connect('shared_memory.db')
    data = {"description": "A skill related to neural networks"}
    insert_new_skill(conn, "neural_networks_skill", data)
    conn.close()

if __name__ == "__main__":
    main()