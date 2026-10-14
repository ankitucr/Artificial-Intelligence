# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_81.py", line 22, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_81.py", line 19, in main
    print(get_skill(new_skill_name))
          ~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_81.py", line 12, in get_skill
    c.execute("SELECT description FROM skills WHERE name=?", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: no such column: description


import sqlite3

conn = sqlite3.connect('shared_memory.db')
c = conn.cursor()

def add_skill(skill_name, skill_description):
    c.execute("CREATE TABLE IF NOT EXISTS skills (name TEXT, description TEXT)")
    c.execute("INSERT INTO skills VALUES (?,?)", (skill_name, skill_description))
    conn.commit()

def get_skill(skill_name):
    c.execute("SELECT description FROM skills WHERE name=?", (skill_name,))
    return c.fetchone()

def main():
    new_skill_name = 'web_search'
    new_skill_description = 'ability to query duckduckgo'
    add_skill(new_skill_name, new_skill_description)
    print(get_skill(new_skill_name))

if __name__ == "__main__":
    main()