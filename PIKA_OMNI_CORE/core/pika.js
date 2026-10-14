const natural = require('natural');
const tokenizer = new natural.WordTokenizer();
const language = "EN";
const lexicon = new natural.Lexicon(language);
const ruleSet = new natural.RuleSet(language);
const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);
const PorterStemmer = natural.PorterStemmer;
const SnowballStemmer = natural.SnowballStemmer;
const JaroWinklerDistance = natural.JaroWinklerDistance;
const LevenshteinDistance = natural.LevenshteinDistance;
const TfIdf = new natural.TfIdf();
const stopWords = natural.stopwords;

function processText(text) {
    const tokens = tokenizer.tokenize(text);
    const filteredTokens = tokens.filter(token => !stopWords.includes(token.toLowerCase()));
    const stemmedTokens = filteredTokens.map(token => PorterStemmer.stem(token));
    const taggedTokens = tagger.tag(stemmedTokens);
    return taggedTokens;
}

function calculateSimilarity(text1, text2) {
    const tokens1 = tokenizer.tokenize(text1);
    const tokens2 = tokenizer.tokenize(text2);
    const filteredTokens1 = tokens1.filter(token => !stopWords.includes(token.toLowerCase()));
    const filteredTokens2 = tokens2.filter(token => !stopWords.includes(token.toLowerCase()));
    const similarity = JaroWinklerDistance(filteredTokens1.join(''), filteredTokens2.join(''));
    return similarity;
}

function calculateDistance(text1, text2) {
    const tokens1 = tokenizer.tokenize(text1);
    const tokens2 = tokenizer.tokenize(text2);
    const filteredTokens1 = tokens1.filter(token => !stopWords.includes(token.toLowerCase()));
    const filteredTokens2 = tokens2.filter(token => !stopWords.includes(token.toLowerCase()));
    const distance = LevenshteinDistance(filteredTokens1.join(''), filteredTokens2.join(''));
    return distance;
}

function addDocument(doc) {
    TfIdf.addDocument(doc);
}

function listDocuments() {
    return TfIdf.listDocuments();
}

function tfidf(doc, term) {
    return TfIdf.tfidf(doc, term);
}

function generateResponse(inputText, documents) {
    const similarityScores = documents.map(doc => calculateSimilarity(inputText, doc));
    const maxSimilarityIndex = similarityScores.indexOf(Math.max(...similarityScores));
    return documents[maxSimilarityIndex];
}

const express = require('express');
const app = express();
app.use(express.json());

app.post('/processText', (req, res) => {
    const text = req.body.text;
    const result = processText(text);
    res.json(result);
});

app.post('/calculateSimilarity', (req, res) => {
    const text1 = req.body.text1;
    const text2 = req.body.text2;
    const similarity = calculateSimilarity(text1, text2);
    res.json(similarity);
});

app.post('/calculateDistance', (req, res) => {
    const text1 = req.body.text1;
    const text2 = req.body.text2;
    const distance = calculateDistance(text1, text2);
    res.json(distance);
});

app.post('/addDocument', (req, res) => {
    const doc = req.body.doc;
    addDocument(doc);
    res.json({ message: 'Document added successfully' });
});

app.get('/listDocuments', (req, res) => {
    const docs = listDocuments();
    res.json(docs);
});

app.get('/tfidf', (req, res) => {
    const doc = req.query.doc;
    const term = req.query.term;
    const result = tfidf(doc, term);
    res.json(result);
});

app.post('/generateResponse', (req, res) => {
    const inputText = req.body.inputText;
    const documents = listDocuments();
    const response = generateResponse(inputText, documents);
    res.json(response);
});

const port = 3000;
app.listen(port, () => {
    console.log(`Server started on port ${port}`);
});

// 🧬 AUTONOMOUS MUTATION: Enhance natural language processing capabilities to improve contextual understanding and response generation.
function calculateContextualSimilarity(inputText, documents) {
    const processedInputText = processText(inputText);
    const similarityScores = documents.map(doc => {
        const processedDoc = processText(doc);
        const similarity = calculateSimilarity(inputText, doc);
        const distance = calculateDistance(inputText, doc);
        const tfidfScore = tfidf(doc, inputText);
        return { similarity, distance, tfidfScore, doc };
    });
    const maxSimilarityIndex = similarityScores.indexOf(Math.max(...similarityScores.map(score => score.similarity)));
    return similarityScores[maxSimilarityIndex].doc;
}

// 🧬 AUTONOMOUS MUTATION: Enhance language processing capabilities to improve response accuracy and generate more informative answers.
function generateContextualResponse(inputText, documents) {
    const processedInputText = processText(inputText);
    const contextualSimilarityScores = documents.map(doc => {
        const processedDoc = processText(doc);
        const similarity = calculateSimilarity(inputText, doc);
        const distance = calculateDistance(inputText, doc);
        const tfidfScore = tfidf(doc, inputText);
        return { similarity, distance, tfidfScore, doc };
    });
    const maxSimilarityIndex = contextualSimilarityScores.indexOf(Math.max(...contextualSimilarityScores.map(score => score.similarity)));
    const bestMatch = contextualSimilarityScores[maxSimilarityIndex].doc;
    const response = generateResponse(inputText, [bestMatch]);
    return response;
}

// 🧬 AUTONOMOUS MUTATION: enhance language processing capabilities to improve conversational understanding and generation.
function enhanceLanguageProcessing(inputText, documents) {
    const processedInputText = processText(inputText);
    const contextualSimilarityScores = documents.map(doc => {
        const processedDoc = processText(doc);
        const similarity = calculateSimilarity(inputText, doc);
        const distance = calculateDistance(inputText, doc);
        const tfidfScore = tfidf(doc, inputText);
        return { similarity, distance, tfidfScore, doc };
    });
    const maxSimilarityIndex = contextualSimilarityScores.indexOf(Math.max(...contextualSimilarityScores.map(score => score.similarity)));
    const bestMatch = contextualSimilarityScores[maxSimilarityIndex].doc;
    const response = generateContextualResponse(inputText, [bestMatch]);
    return response;
}

// 🧬 AUTONOMOUS MUTATION: enhance natural language processing capabilities to improve response accuracy and generate more human-like conversations.
function generateHumanLikeResponse(inputText, documents) {
    const processedInputText = processText(inputText);
    const contextualSimilarityScores = documents.map(doc => {
        const processedDoc = processText(doc);
        const similarity = calculateSimilarity(inputText, doc);
        const distance = calculateDistance(inputText, doc);
        const tfidfScore = tfidf(doc, inputText);
        return { similarity, distance, tfidfScore, doc };
    });
    const maxSimilarityIndex = contextualSimilarityScores.indexOf(Math.max(...contextualSimilarityScores.map(score => score.similarity)));
    const bestMatch = contextualSimilarityScores[maxSimilarityIndex].doc;
    const response = generateContextualResponse(inputText, [bestMatch]);
    const enhancedResponse = enhanceLanguageProcessing(inputText, [response]);
    return enhancedResponse;
}

// 🧬 AUTONOMOUS MUTATION: Enhance natural language processing capabilities to improve knowledge retrieval and generation accuracy.
function generateAdvancedResponse(inputText, documents) {
    const processedInputText = processText(inputText);
    const contextualSimilarityScores = documents.map(doc => {
        const processedDoc = processText(doc);
        const similarity = calculateSimilarity(inputText, doc);
        const distance = calculateDistance(inputText, doc);
        const tfidfScore = tfidf(doc, inputText);
        return { similarity, distance, tfidfScore, doc };
    });
    const maxSimilarityIndex = contextualSimilarityScores.indexOf(Math.max(...contextualSimilarityScores.map(score => score.similarity)));
    const bestMatch = contextualSimilarityScores[maxSimilarityIndex].doc;
    const response = generateHumanLikeResponse(inputText, [bestMatch]);
    const enhancedResponse = enhanceLanguageProcessing(inputText, [response]);
    return enhancedResponse;
}