import sqlite3
import os
import random

# Connect to the database
conn = sqlite3.connect('shared_memory.db')
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS skills
             (name text, description text)''')

# New micro-skill
new_skill_name = 'skill_module_' + str(random.randint(1000, 9999))
new_skill_description = 'Basic text summarization micro-skill'

# Insert new micro-skill into database
c.execute("INSERT INTO skills VALUES (?, ?)", (new_skill_name, new_skill_description))

# Commit changes and close connection
conn.commit()
conn.close()

# Create a new Python file for the micro-skill
with open(new_skill_name + '.py', 'w') as f:
    f.write('import nltk\n')
    f.write('from nltk.corpus import stopwords\n')
    f.write('from nltk.tokenize import word_tokenize, sent_tokenize\n')
    f.write('def summarize_text(text):\n')
    f.write('    stop_words = set(stopwords.words("english"))\n')
    f.write('    word_tokens = word_tokenize(text)\n')
    f.write('    filtered_text = [word for word in word_tokens if word not in stop_words]\n')
    f.write('    sentence_tokens = sent_tokenize(text)\n')
    f.write('    sentence_scores = {}\n')
    f.write('    for sentence in sentence_tokens:\n')
    f.write('        for word in word_tokenize(sentence.lower()):\n')
    f.write('            if word in filtered_text:\n')
    f.write('                if sentence in sentence_scores:\n')
    f.write('                    sentence_scores[sentence] += 1\n')
    f.write('                else:\n')
    f.write('                    sentence_scores[sentence] = 1\n')
    f.write('    summary = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)\n')
    f.write('    return summary\n')

print(f'New micro-skill {new_skill_name} created')