# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_71.py", line 44, in <module>
    add_micro_skill('web_scraper')
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_71.py", line 12, in add_micro_skill
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import requests
from bs4 import BeautifulSoup

def add_micro_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text)''')

    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def retrieve_micronet():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()

    c.execute("SELECT * FROM skills")
    skills = c.fetchall()
    conn.close()
    return skills

def micronet_expansion(skill_name):
    url = f"https://duckduckgo.com/html/?q={skill_name}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.text

def neural_node_init():
    import numpy as np
    node_weights = np.random.rand(10)
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS neural_nodes
                 (weights blob)''')

    c.execute("INSERT INTO neural_nodes VALUES (?)", (node_weights.tobytes(),))
    conn.commit()
    conn.close()

add_micro_skill('web_scraper')
neural_node_init()
print(retrieve_micronet())