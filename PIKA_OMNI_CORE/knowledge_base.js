const express = require('express');
const app = express();
const port = 3000;
const axios = require('axios');
const natural = require('natural');
const stopwords = require('stopwords').english;
const WordTokenizer = new natural.WordTokenizer();
const TfIdf = new natural.TfIdf();

app.use(express.json());

let documents = [];

app.post('/add-document', (req, res) => {
    const document = req.body.document;
    documents.push(document);
    TfIdf.addDocument(document);
    res.send(`Document added: ${document}`);
});

app.post('/search', (req, res) => {
    const query = req.body.query;
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const results = TfIdf.listTerms(0);
    const scoredResults = results.filter(result => filteredQuery.includes(result.term));
    scoredResults.sort((a, b) => b.tfidf - a.tfidf);
    res.send(scoredResults);
});

app.post('/generate', (req, res) => {
    const prompt = req.body.prompt;
    const tokenizedPrompt = WordTokenizer.tokenize(prompt);
    const filteredPrompt = tokenizedPrompt.filter(word => !stopwords.includes(word.toLowerCase()));
    const generatedText = '';
    const words = documents.join(' ').split(' ');
    const wordMap = {};
    words.forEach(word => {
        if (!wordMap[word]) {
            wordMap[word] = [];
        }
        wordMap[word].push(words[words.indexOf(word) + 1]);
    });
    let currentWord = filteredPrompt[0];
    for (let i = 0; i < 100; i++) {
        if (wordMap[currentWord]) {
            currentWord = wordMap[currentWord][Math.floor(Math.random() * wordMap[currentWord].length)];
            generatedText += ' ' + currentWord;
        } else {
            break;
        }
    }
    res.send(generatedText);
});

app.listen(port, () => {
    console.log(`Server listening on port ${port}`);
});

// 🧬 AUTONOMOUS MUTATION: to improve performance and expand domain-specific expertise.
function generateSummary(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const summary = [];
    documents.forEach(document => {
        const tokenizedDocument = WordTokenizer.tokenize(document);
        const filteredDocument = tokenizedDocument.filter(word => !stopwords.includes(word.toLowerCase()));
        const similarity = filteredQuery.filter(word => filteredDocument.includes(word)).length;
        if (similarity > 0) {
            summary.push({ document, similarity });
        }
    });
    summary.sort((a, b) => b.similarity - a.similarity);
    return summary.slice(0, 5).map(item => item.document);
}

// 🧬 AUTONOMOUS MUTATION: to improve language processing capabilities and enhance overall system performance.
function expandDomainKnowledge(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const relatedDocuments = documents.filter(document => {
        const tokenizedDocument = WordTokenizer.tokenize(document);
        const filteredDocument = tokenizedDocument.filter(word => !stopwords.includes(word.toLowerCase()));
        return filteredQuery.some(word => filteredDocument.includes(word));
    });
    const newTerms = relatedDocuments.reduce((acc, document) => {
        const tokenizedDocument = WordTokenizer.tokenize(document);
        const filteredDocument = tokenizedDocument.filter(word => !stopwords.includes(word.toLowerCase()));
        return [...acc, ...filteredDocument];
    }, []);
    const uniqueTerms = [...new Set(newTerms)];
    return uniqueTerms;
}

// 🧬 AUTONOMOUS MUTATION: to improve natural language understanding and generation capabilities, and expand domain-specific knowledge repositories.
function enhanceLanguageUnderstanding(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const enhancedQuery = filteredQuery.map(word => {
        const relatedWords = documents.reduce((acc, document) => {
            const tokenizedDocument = WordTokenizer.tokenize(document);
            const filteredDocument = tokenizedDocument.filter(w => !stopwords.includes(w.toLowerCase()));
            if (filteredDocument.includes(word)) {
                return [...acc, ...filteredDocument];
            }
            return acc;
        }, []);
        const uniqueRelatedWords = [...new Set(relatedWords)];
        return { word, relatedWords: uniqueRelatedWords };
    });
    return enhancedQuery;
}

// 🧬 AUTONOMOUS MUTATION: to improve response accuracy and incorporate new information sources
function integrateNewInformationSources(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const newSources = [];
    filteredQuery.forEach(word => {
        axios.get(`https://en.wikipedia.org/w/api.php?action=opensearch&search=${word}&limit=5&format=json`)
            .then(response => {
                const data = response.data;
                const titles = data[1];
                titles.forEach(title => {
                    axios.get(`https://en.wikipedia.org/w/api.php?action=parse&page=${title}&format=json`)
                        .then(response => {
                            const data = response.data;
                            const text = data.parse.text['*'];
                            newSources.push(text);
                        })
                        .catch(error => {
                            console.error(error);
                        });
                });
            })
            .catch(error => {
                console.error(error);
            });
    });
    return newSources;
}

// 🧬 AUTONOMOUS MUTATION: enhance_language_understanding_and_generation_capabilities
function generateTextBasedOnQuery(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const wordMap = {};
    documents.forEach(document => {
        const tokenizedDocument = WordTokenizer.tokenize(document);
        tokenizedDocument.forEach((word, index) => {
            if (index < tokenizedDocument.length - 1) {
                if (!wordMap[word]) {
                    wordMap[word] = [];
                }
                wordMap[word].push(tokenizedDocument[index + 1]);
            }
        });
    });
    let currentWord = filteredQuery[0];
    let generatedText = currentWord;
    for (let i = 0; i < 100; i++) {
        if (wordMap[currentWord]) {
            currentWord = wordMap[currentWord][Math.floor(Math.random() * wordMap[currentWord].length)];
            generatedText += ' ' + currentWord;
        } else {
            break;
        }
    }
    return generatedText;
}

// 🧬 AUTONOMOUS MUTATION: enhance language understanding and generation capabilities to improve overall performance and accuracy.
function advancedTextGeneration(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const wordMap = {};
    documents.forEach(document => {
        const tokenizedDocument = WordTokenizer.tokenize(document);
        tokenizedDocument.forEach((word, index) => {
            if (index < tokenizedDocument.length - 1) {
                if (!wordMap[word]) {
                    wordMap[word] = [];
                }
                wordMap[word].push(tokenizedDocument[index + 1]);
            }
        });
    });
    let currentWord = filteredQuery[0];
    let generatedText = currentWord;
    for (let i = 0; i < 100; i++) {
        if (wordMap[currentWord]) {
            currentWord = wordMap[currentWord][Math.floor(Math.random() * wordMap[currentWord].length)];
            generatedText += ' ' + currentWord;
        } else {
            break;
        }
    }
    const enhancedQuery = enhanceLanguageUnderstanding(documents, query);
    const relatedWords = enhancedQuery.map(item => item.relatedWords);
    const allRelatedWords = relatedWords.flat();
    const uniqueRelatedWords = [...new Set(allRelatedWords)];
    const additionalText = uniqueRelatedWords.slice(0, 10).join(' ');
    return generatedText + ' ' + additionalText;
}

// 🧬 AUTONOMOUS MUTATION: enhance natural language processing capabilities to improve response accuracy and generation of more informative answers.
function intelligentResponseGeneration(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const summary = generateSummary(documents, query);
    const expandedDomainKnowledge = expandDomainKnowledge(documents, query);
    const enhancedQuery = enhanceLanguageUnderstanding(documents, query);
    const generatedText = advancedTextGeneration(documents, query);
    const integratedNewInformationSources = integrateNewInformationSources(documents, query);
    const response = {
        summary: summary,
        expandedDomainKnowledge: expandedDomainKnowledge,
        enhancedQuery: enhancedQuery,
        generatedText: generatedText,
        integratedNewInformationSources: integratedNewInformationSources
    };
    return response;
}

// 🧬 AUTONOMOUS MUTATION: to improve natural language processing and enhance overall performance.
function advancedNaturalLanguageProcessing(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const wordMap = {};
    documents.forEach(document => {
        const tokenizedDocument = WordTokenizer.tokenize(document);
        tokenizedDocument.forEach((word, index) => {
            if (index < tokenizedDocument.length - 1) {
                if (!wordMap[word]) {
                    wordMap[word] = [];
                }
                wordMap[word].push(tokenizedDocument[index + 1]);
            }
        });
    });
    let currentWord = filteredQuery[0];
    let generatedText = currentWord;
    for (let i = 0; i < 100; i++) {
        if (wordMap[currentWord]) {
            currentWord = wordMap[currentWord][Math.floor(Math.random() * wordMap[currentWord].length)];
            generatedText += ' ' + currentWord;
        } else {
            break;
        }
    }
    const enhancedQuery = enhanceLanguageUnderstanding(documents, query);
    const relatedWords = enhancedQuery.map(item => item.relatedWords);
    const allRelatedWords = relatedWords.flat();
    const uniqueRelatedWords = [...new Set(allRelatedWords)];
    const additionalText = uniqueRelatedWords.slice(0, 10).join(' ');
    const response = {
        generatedText: generatedText + ' ' + additionalText,
        relatedWords: uniqueRelatedWords,
        enhancedQuery: enhancedQuery
    };
    return response;
}

// 🧬 AUTONOMOUS MUTATION: enhance language understanding and generation capabilities to improve overall performance and accuracy.
function enhancedNaturalLanguageGeneration(documents, query) {
    const tokenizedQuery = WordTokenizer.tokenize(query);
    const filteredQuery = tokenizedQuery.filter(word => !stopwords.includes(word.toLowerCase()));
    const wordMap = {};
    documents.forEach(document => {
        const tokenizedDocument = WordTokenizer.tokenize(document);
        tokenizedDocument.forEach((word, index) => {
            if (index < tokenizedDocument.length - 1) {
                if (!wordMap[word]) {
                    wordMap[word] = [];
                }
                wordMap[word].push(tokenizedDocument[index + 1]);
            }
        });
    });
    let currentWord = filteredQuery[0];
    let generatedText = currentWord;
    for (let i = 0; i < 100; i++) {
        if (wordMap[currentWord]) {
            currentWord = wordMap[currentWord][Math.floor(Math.random() * wordMap[currentWord].length)];
            generatedText += ' ' + currentWord;
        } else {
            break;
        }
    }
    const enhancedQuery = enhanceLanguageUnderstanding(documents, query);
    const relatedWords = enhancedQuery.map(item => item.relatedWords);
    const allRelatedWords = relatedWords.flat();
    const uniqueRelatedWords = [...new Set(allRelatedWords)];
    const additionalText = uniqueRelatedWords.slice(0, 10).join(' ');
    const finalText = generatedText + ' ' + additionalText;
    return finalText;
}