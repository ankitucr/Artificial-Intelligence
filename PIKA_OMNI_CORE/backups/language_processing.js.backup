const natural = require('natural');
const stopwords = require('stopwords').english;
const PorterStemmer = natural.PorterStemmer;
const Tokenizer = new natural.WordTokenizer();
const TfIdf = new natural.TfIdf();

class ContextualUnderstanding {
  constructor() {
    this.tfidf = new TfIdf();
  }

  tokenizeText(text) {
    return Tokenizer.tokenize(text);
  }

  removeStopwords(tokens) {
    return tokens.filter(token => !stopwords.includes(token.toLowerCase()));
  }

  stemTokens(tokens) {
    return tokens.map(token => PorterStemmer.stem(token));
  }

  calculateTfIdf(text) {
    const tokens = this.tokenizeText(text);
    const filteredTokens = this.removeStopwords(tokens);
    const stemmedTokens = this.stemTokens(filteredTokens);
    this.tfidf.addDocument(stemmedTokens.join(' '));
    return this.tfidf.tfidf(stemmedTokens.join(' '), 0);
  }

  compareContexts(context1, context2) {
    const tfIdf1 = this.calculateTfIdf(context1);
    const tfIdf2 = this.calculateTfIdf(context2);
    const similarity = this.calculateSimilarity(tfIdf1, tfIdf2);
    return similarity;
  }

  calculateSimilarity(tfIdf1, tfIdf2) {
    const dotProduct = tfIdf1.reduce((acc, val, index) => acc + val * tfIdf2[index], 0);
    const magnitude1 = Math.sqrt(tfIdf1.reduce((acc, val) => acc + val * val, 0));
    const magnitude2 = Math.sqrt(tfIdf2.reduce((acc, val) => acc + val * val, 0));
    return dotProduct / (magnitude1 * magnitude2);
  }
}

module.exports = ContextualUnderstanding;