const natural = require('natural');
const express = require('express');
const app = express();
const port = 3000;

app.use(express.json());

let tokenizer = new natural.WordTokenizer();
let language = "EN";
let lexicon = new natural.Lexicon(language);
let ruleSet = new natural.RuleSet(language);
let tagger = new natural.BrillPOSTagger(lexicon, ruleSet);

let context = {};

app.post('/process', (req, res) => {
    let text = req.body.text;
    let tokens = tokenizer.tokenize(text);
    let taggedTokens = tagger.tag(tokens);

    let intent = getIntent(taggedTokens);
    let entities = getEntities(taggedTokens);

    let response = generateResponse(intent, entities, context);

    res.json({ response: response });
});

function getIntent(taggedTokens) {
    let intent = null;
    for (let i = 0; i < taggedTokens.length; i++) {
        if (taggedTokens[i][1] === 'NN') {
            intent = taggedTokens[i][0];
            break;
        }
    }
    return intent;
}

function getEntities(taggedTokens) {
    let entities = [];
    for (let i = 0; i < taggedTokens.length; i++) {
        if (taggedTokens[i][1] === 'NNP') {
            entities.push(taggedTokens[i][0]);
        }
    }
    return entities;
}

function generateResponse(intent, entities, context) {
    let response = '';
    if (intent === 'greeting') {
        response = 'Hello, how can I assist you today?';
    } else if (intent === 'goodbye') {
        response = 'Goodbye, it was nice talking to you.';
    } else {
        response = 'I did not understand your request.';
    }

    if (entities.length > 0) {
        response += ' You mentioned ' + entities.join(', ');
    }

    return response;
}

app.listen(port, () => {
    console.log(`Server listening on port ${port}`);
});

// 🧬 AUTONOMOUS MUTATION: enhancement_of_natural_language_processing_capabilities
function enhanceNLP(text) {
    let tokens = tokenizer.tokenize(text);
    let taggedTokens = tagger.tag(tokens);
    let intent = getIntent(taggedTokens);
    let entities = getEntities(taggedTokens);
    let response = generateResponse(intent, entities, context);
    return response;
}

// 🧬 AUTONOMOUS MUTATION: Enhance natural language processing capabilities to better understand and respond to complex user queries.
function advancedNLP(text) {
    let tokens = tokenizer.tokenize(text);
    let taggedTokens = tagger.tag(tokens);
    let intent = getIntent(taggedTokens);
    let entities = getEntities(taggedTokens);

    let sentiment = getSentiment(taggedTokens);
    let contextUpdate = updateContext(intent, entities, context);

    let response = generateAdvancedResponse(intent, entities, sentiment, contextUpdate);
    return response;
}

function getSentiment(taggedTokens) {
    let sentiment = 0;
    for (let i = 0; i < taggedTokens.length; i++) {
        if (taggedTokens[i][1] === 'JJ') {
            if (taggedTokens[i][0] === 'good' || taggedTokens[i][0] === 'great') {
                sentiment += 1;
            } else if (taggedTokens[i][0] === 'bad' || taggedTokens[i][0] === 'terrible') {
                sentiment -= 1;
            }
        }
    }
    return sentiment;
}

function updateContext(intent, entities, context) {
    if (intent === 'greeting') {
        context.greetingCount = (context.greetingCount || 0) + 1;
    } else if (intent === 'goodbye') {
        context.goodbyeCount = (context.goodbyeCount || 0) + 1;
    }
    context.entities = entities;
    return context;
}

function generateAdvancedResponse(intent, entities, sentiment, context) {
    let response = '';
    if (intent === 'greeting') {
        response = 'Hello, how can I assist you today?';
    } else if (intent === 'goodbye') {
        response = 'Goodbye, it was nice talking to you.';
    } else {
        response = 'I did not understand your request.';
    }

    if (entities.length > 0) {
        response += ' You mentioned ' + entities.join(', ');
    }

    if (sentiment > 0) {
        response += ' I sense a positive tone in your message.';
    } else if (sentiment < 0) {
        response += ' I sense a negative tone in your message.';
    }

    if (context.greetingCount > 1) {
        response += ' You have greeted me ' + context.greetingCount + ' times.';
    }

    if (context.goodbyeCount > 1) {
        response += ' You have said goodbye ' + context.goodbyeCount + ' times.';
    }

    return response;
}

// 🧬 AUTONOMOUS MUTATION: to enhance knowledge graph expansion and improve response generation capabilities
function expandKnowledgeGraph(entities, context) {
    let graph = {};
    for (let entity of entities) {
        graph[entity] = {};
        if (context.entities) {
            for (let existingEntity of context.entities) {
                if (existingEntity !== entity) {
                    graph[entity][existingEntity] = 'related';
                }
            }
        }
    }
    context.graph = graph;
    return context;
}