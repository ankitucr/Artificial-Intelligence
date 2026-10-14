# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_57.py", line 62, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_57.py", line 58, in main
    register_skill_module(filename)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_57.py", line 16, in register_skill_module
    c.execute("INSERT OR IGNORE INTO skills (filename) VALUES (?)", (filename,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named filename


import sqlite3
import os
import hashlib

def create_skill_module(skill_name, skill_code):
    skill_id = hashlib.sha256(skill_name.encode()).hexdigest()
    filename = f"skill_module_{skill_id}.py"
    with open(filename, "w") as f:
        f.write(skill_code)
    return filename

def register_skill_module(filename):
    conn = sqlite3.connect("shared_memory.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS skills (filename TEXT PRIMARY KEY)")
    c.execute("INSERT OR IGNORE INTO skills (filename) VALUES (?)", (filename,))
    conn.commit()
    conn.close()

def get_skill_code():
    skill_name = "text_summarization"
    skill_code = """
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

def summarize_text(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    freq_table = {}
    for word in words:
        word = word.lower()
        if word in stop_words:
            continue
        if word in freq_table:
            freq_table[word] += 1
        else:
            freq_table[word] = 1
    max_freq = max(freq_table.values())
    for word in freq_table.keys():
        freq_table[word] = (freq_table[word]/max_freq)
    sentence_scores = {}
    for sentence in sent_tokenize(text):
        for word in word_tokenize(sentence.lower()):
            if word in freq_table:
                if sentence in sentence_scores:
                    sentence_scores[sentence] += freq_table[word]
                else:
                    sentence_scores[sentence] = freq_table[word]
    summary_sentences = heapq.nlargest(5, sentence_scores, key=sentence_scores.get)
    return ' '.join(summary_sentences)
"""
    return skill_name, skill_code

def main():
    skill_name, skill_code = get_skill_code()
    filename = create_skill_module(skill_name, skill_code)
    register_skill_module(filename)
    print(f"Created and registered new skill module: {filename}")

if __name__ == "__main__":
    main()