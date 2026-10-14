# skill_module_f1bcbec0eddb40f2923dc7604139741c.py
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
def summarize_text(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [word for word in word_tokens if word not in stop_words]
    return ' '.join(filtered_text)
