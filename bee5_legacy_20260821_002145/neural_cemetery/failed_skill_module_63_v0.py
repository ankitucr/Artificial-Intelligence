# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_63.py", line 22, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_63.py", line 18, in main
    insert_new_skill(conn, "neural_networks_skill", data)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_63.py", line 11, in insert_new_skill
    c.execute("INSERT INTO skills (name, data) VALUES (?,?)", (skill_name, str(skill_data)))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named data


import sqlite3
import requests

def fetch_duckduckgo_data(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
    response = requests.get(url)
    return response.json()

def insert_new_skill(conn, skill_name, skill_data):
    c = conn.cursor()
    c.execute("INSERT INTO skills (name, data) VALUES (?,?)", (skill_name, str(skill_data)))
    conn.commit()

def main():
    conn = sqlite3.connect('shared_memory.db')
    query = "neural networks"
    data = fetch_duckduckgo_data(query)
    insert_new_skill(conn, "neural_networks_skill", data)
    conn.close()

if __name__ == "__main__":
    main()