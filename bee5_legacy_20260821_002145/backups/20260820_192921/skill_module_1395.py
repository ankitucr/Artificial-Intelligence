import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
def summarize_text(text):
    stop_words = set(stopwords.words("english"))
    word_tokens = word_tokenize(text)
    filtered_text = [word for word in word_tokens if word not in stop_words]
    sentence_tokens = sent_tokenize(text)
    sentence_scores = {}
    for sentence in sentence_tokens:
        for word in word_tokenize(sentence.lower()):
            if word in filtered_text:
                if sentence in sentence_scores:
                    sentence_scores[sentence] += 1
                else:
                    sentence_scores[sentence] = 1
    summary = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
    return summary
