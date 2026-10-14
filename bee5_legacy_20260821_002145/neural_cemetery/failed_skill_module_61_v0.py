# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_61.py", line 31, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_61.py", line 25, in main
    add_micro_skill()
    ~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_61.py", line 21, in add_micro_skill
    add_skill(skill_name)
    ~~~~~~~~~^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_61.py", line 10, in add_skill
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import requests

def add_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                skill_name text
                )""")
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def fetch_duckduckgo(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    response = requests.get(url)
    return response.json()

def add_micro_skill():
    skill_name = "web_search"
    add_skill(skill_name)
    print(f"Added skill: {skill_name}")

def main():
    add_micro_skill()
    query = "python neural network"
    result = fetch_duckduckgo(query)
    print(result)

if __name__ == "__main__":
    main()