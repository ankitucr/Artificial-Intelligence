# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_62.py", line 38, in <module>
    print(add_skill(new_skill))
          ~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_62.py", line 25, in add_skill
    add_micro_skill(skill_name)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_62.py", line 10, in add_micro_skill
    c.execute("INSERT OR IGNORE INTO micro_skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table micro_skills has 2 columns but 1 values were supplied


import sqlite3
import requests
from bs4 import BeautifulSoup

def add_micro_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS micro_skills
                 (name text PRIMARY KEY)''')
    c.execute("INSERT OR IGNORE INTO micro_skills VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def fetch_definition(skill_name):
    url = f"https://duckduckgo.com/html/?q={skill_name}+definition"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    definition = soup.find('a', class_='result__a')
    if definition:
        return definition.text
    else:
        return None

def add_skill(skill_name):
    add_micro_skill(skill_name)
    definition = fetch_definition(skill_name)
    if definition:
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS skill_definitions
                     (name text PRIMARY KEY, definition text)''')
        c.execute("INSERT OR IGNORE INTO skill_definitions VALUES (?, ?)", (skill_name, definition))
        conn.commit()
        conn.close()
    return definition

new_skill = 'web_scraping'
print(add_skill(new_skill))