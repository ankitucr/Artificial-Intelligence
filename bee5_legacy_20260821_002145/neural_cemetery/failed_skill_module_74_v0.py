# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_74.py", line 40, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_74.py", line 32, in main
    add_skill(new_skill)
    ~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_74.py", line 11, in add_skill
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import requests
from bs4 import BeautifulSoup

def add_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                skill_name text
                )""")
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

def web_search(query):
    url = "https://duckduckgo.com/html"
    params = {"q": query}
    response = requests.post(url, data=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.find_all('a', class_='result__a')

def main():
    new_skill = "web_search"
    add_skill(new_skill)
    print(get_skills())
    query = "python programming"
    results = web_search(query)
    for result in results:
        print(result.text)

if __name__ == "__main__":
    main()