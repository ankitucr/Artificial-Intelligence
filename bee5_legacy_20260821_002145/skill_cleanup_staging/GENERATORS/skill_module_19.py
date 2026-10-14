import sqlite3
import webbrowser

def add_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (skill_name text, skill_description text)''')
    c.execute("INSERT INTO skills VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def suggest_next_skill(failed_attempts):
    next_skill = ""
    if failed_attempts < 100:
        next_skill = "basic_web_scraping"
    elif failed_attempts < 200:
        next_skill = "neural_network_node"
    else:
        next_skill = "advanced_text_processing"
    return next_skill

def learn_new_skill(skill_name):
    if skill_name == "basic_web_scraping":
        webbrowser.open("https://docs.python.org/3/library/urllib.html")
    elif skill_name == "neural_network_node":
        webbrowser.open("https://www.tensorflow.org/tutorials")
    elif skill_name == "advanced_text_processing":
        webbrowser.open("https://www.nltk.org/book/")

def main():
    failed_attempts = 152
    next_skill = suggest_next_skill(failed_attempts)
    add_skill(next_skill, "ability to read from duckduckgo and create a basic neural network node")
    learn_new_skill(next_skill)

if __name__ == "__main__":
    main()