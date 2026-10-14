import sqlite3

def add_skill(skill_name, skill_type):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?,?)", (skill_name, skill_type))
    conn.commit()
    conn.close()

def add_micro_skill():
    skill_name = "Micro Skill"
    skill_type = "Type A"
    add_skill(skill_name, skill_type)

def main():
    add_micro_skill()

if __name__ == "__main__":
    main()