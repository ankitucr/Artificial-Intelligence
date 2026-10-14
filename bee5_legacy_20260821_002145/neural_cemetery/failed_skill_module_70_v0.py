# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_70.py", line 43, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_70.py", line 33, in main
    add_skill(new_skill)
    ~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_70.py", line 9, in add_skill
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import requests

def add_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills
                 (name text)""")
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def get_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skills")
    skills = c.fetchall()
    conn.close()
    return skills

def fetch_data_from_duckduckgo(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    response = requests.get(url)
    return response.json()

def create_neural_network_node():
    import numpy as np
    weights = np.random.rand(10)
    return weights

def main():
    new_skill = "web_search"
    add_skill(new_skill)
    skills = get_skills()
    print(skills)
    query = "python programming"
    data = fetch_data_from_duckduckgo(query)
    print(data)
    node = create_neural_network_node()
    print(node)

if __name__ == "__main__":
    main()