import sqlite3

def register_skill_module(skill_module_name, skill_module_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS skill_modules (name TEXT, description TEXT)")
    c.execute("INSERT INTO skill_modules VALUES (?, ?)", (skill_module_name, skill_module_description))
    conn.commit()
    conn.close()

def get_skill_modules():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skill_modules")
    return c.fetchall()

new_skill_module = "module_1"
new_skill_module_description = "description_1"
register_skill_module(new_skill_module, new_skill_module_description)
print(get_skill_modules())