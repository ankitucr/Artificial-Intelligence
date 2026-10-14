# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_76.py", line 18, in <module>
    add_web_scraping_skill()
    ~~~~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_76.py", line 14, in add_web_scraping_skill
    create_skill('web_scraping')
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_76.py", line 9, in create_skill
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import requests

def create_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text)''')
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def add_web_scraping_skill():
    create_skill('web_scraping')
    response = requests.get('https://duckduckgo.com')
    print(f"Web scraping skill added. Successful response from DuckDuckGo: {response.status_code}")

add_web_scraping_skill()