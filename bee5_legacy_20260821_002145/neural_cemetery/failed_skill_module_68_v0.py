# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_68.py", line 36, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_68.py", line 28, in main
    add_skill(new_skill)
    ~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_68.py", line 9, in add_skill
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import requests

def add_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text)''')
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def get_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skills")
    skills = c.fetchall()
    conn.close()
    return [skill[0] for skill in skills]

def fetch_duckduckgo(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    response = requests.get(url)
    return response.json()

def main():
    new_skill = "web_search"
    add_skill(new_skill)
    skills = get_skills()
    print("Current Active Skills:", skills)
    query = "Python programming"
    result = fetch_duckduckgo(query)
    print("DuckDuckGo Result:", result)

if __name__ == "__main__":
    main()