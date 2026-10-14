# skill_module_419ddd57a6844c969257cf682b801abb.py
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
def summarize_text(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [word for word in word_tokens if word not in stop_words]
    return ' '.join(filtered_text)
