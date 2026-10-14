# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_52.py", line 38, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_52.py", line 34, in main
    new_skill.save_skill()
    ~~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_52.py", line 21, in save_skill
    c.execute("INSERT INTO skills VALUES (?,?,?)",
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              (self.name, self.description, self.filename))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 3 values were supplied


import sqlite3
import os
import hashlib
import random

class MicroSkill:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.filename = self.generate_filename()

    def generate_filename(self):
        hash_object = hashlib.md5(str(random.getrandbits(128)).encode())
        return f"skill_module_{hash_object.hexdigest()}.py"

    def save_skill(self):
        with sqlite3.connect('shared_memory.db') as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS skills
                         (name text, description text, filename text)''')
            c.execute("INSERT INTO skills VALUES (?,?,?)",
                      (self.name, self.description, self.filename))
            conn.commit()

    def write_skill_file(self):
        with open(self.filename, 'w') as f:
            f.write(f"# {self.name}\n")
            f.write(f"# {self.description}\n")
            f.write("import os\n")
            f.write("import sqlite3\n")

def main():
    new_skill = MicroSkill("Basic Text Summarizer", "Summarize text from web pages")
    new_skill.save_skill()
    new_skill.write_skill_file()

if __name__ == "__main__":
    main()