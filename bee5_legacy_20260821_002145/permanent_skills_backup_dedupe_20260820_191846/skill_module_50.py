import sqlite3

class MicroSkill:
    def __init__(self, skill_id, skill_name):
        self.skill_id = skill_id
        self.skill_name = skill_name

    def save_to_db(self):
        connection = sqlite3.connect('shared_memory.db')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO skills VALUES (?,?)', (self.skill_id, self.skill_name))
        connection.commit()
        connection.close()

def main():
    micro_skill = MicroSkill(1, 'Sample Skill')
    micro_skill.save_to_db()

if __name__ == '__main__':
    main()