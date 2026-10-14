# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_52.py", line 22, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_52.py", line 19, in main
    new_skill.save_skill()
    ~~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_52.py", line 13, in save_skill
    c.execute("INSERT INTO skills VALUES (?,?,?)", (self.name, self.description, self.filename))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 3 values were supplied


import sqlite3

class Skill:
    def __init__(self, name, description, filename):
        self.name = name
        self.description = description
        self.filename = filename

    def save_skill(self):
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS skills (name TEXT, description TEXT, filename TEXT)")
        c.execute("INSERT INTO skills VALUES (?,?,?)", (self.name, self.description, self.filename))
        conn.commit()
        conn.close()

def main():
    new_skill = Skill("test_skill", "this is a test skill", "test_skill.py")
    new_skill.save_skill()

if __name__ == "__main__":
    main()