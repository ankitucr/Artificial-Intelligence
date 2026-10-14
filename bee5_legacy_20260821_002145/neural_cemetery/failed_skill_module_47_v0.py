# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_47.py", line 20, in <module>
    add_wikipedia_skill()
    ~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_47.py", line 14, in add_wikipedia_skill
    create_skill_module(skill_name, skill_description)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_47.py", line 7, in create_skill_module
    c.execute("INSERT INTO skills (name, description) VALUES (?, ?)", (skill_name, skill_description))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named description


import sqlite3
import requests

def create_skill_module(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (name, description) VALUES (?, ?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def add_wikipedia_skill():
    skill_name = "Wikipedia Search"
    skill_description = "Search for information on Wikipedia"
    create_skill_module(skill_name, skill_description)
    with open(f"skill_module_{skill_name}.py", "w") as f:
        f.write(f"import wikipedia\n")
        f.write(f"def search_wikipedia(query):\n")
        f.write(f"    return wikipedia.page(query).content\n")

add_wikipedia_skill()