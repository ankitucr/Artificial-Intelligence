import sqlite3
import os
import uuid

def generate_skill_module():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS skill_modules
                 (module_name text, module_description text)''')

    new_module_name = f"skill_module_{uuid.uuid4().hex}.py"
    new_module_description = "Basic text summarization skill"

    c.execute("INSERT INTO skill_modules VALUES (?,?)", (new_module_name, new_module_description))
    conn.commit()
    conn.close()

    with open(new_module_name, 'w') as f:
        f.write(f"# {new_module_name}\n")
        f.write("import nltk\n")
        f.write("from nltk.tokenize import word_tokenize\n")
        f.write("from nltk.corpus import stopwords\n")
        f.write("def summarize_text(text):\n")
        f.write("    stop_words = set(stopwords.words('english'))\n")
        f.write("    word_tokens = word_tokenize(text)\n")
        f.write("    filtered_text = [word for word in word_tokens if word not in stop_words]\n")
        f.write("    return ' '.join(filtered_text)\n")

    return new_module_name

new_module = generate_skill_module()
print(f"New skill module created: {new_module}")