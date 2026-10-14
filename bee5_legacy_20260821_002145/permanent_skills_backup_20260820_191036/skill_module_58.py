import sqlite3
import os

# Create a connection to the database
conn = sqlite3.connect('shared_memory.db')
c = conn.cursor()

# Create table for skills if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS skills
             (name text, description text)''')

# Create a new micro-skill
def create_micro_skill(name, description):
    c.execute("INSERT INTO skills VALUES (?, ?)", (name, description))
    conn.commit()

# Create a new micro-skill for text summarization
create_micro_skill('text_summarization', 'Summarize long pieces of text into shorter summaries')

# Create a basic text summarization function
def summarize_text(text):
    # For now, just return the first 100 characters of the text
    return text[:100]

# Save the new micro-skill to the database
conn.close()

# Create a new Python script for the micro-skill
with open('skill_module_text_summarization.py', 'w') as f:
    f.write('def summarize_text(text):\n')
    f.write('    # For now, just return the first 100 characters of the text\n')
    f.write('    return text[:100]\n')

# Add the new micro-skill to the list of active skills
active_skills = os.listdir()
with open('active_skills.txt', 'w') as f:
    for skill in active_skills:
        if skill.startswith('skill_module_'):
            f.write(skill + '\n')
    f.write('skill_module_text_summarization.py\n')