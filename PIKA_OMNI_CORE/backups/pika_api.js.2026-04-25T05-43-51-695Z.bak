const natural = require('natural');
const express = require('express');
const app = express();
const port = 3000;

app.use(express.json());

const tokenizer = new natural.WordTokenizer();
const language = "EN";
const lexicon = new natural.Lexicon(language);
const ruleSet = new natural.RuleSet(language);
const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);

let knowledgeBase = {
  "greeting": "Hello, how can I assist you today?",
  "goodbye": "It was nice talking to you. Goodbye!",
  "thanks": "You're welcome!",
  "help": "I can assist you with general knowledge and answer your questions."
};

app.post('/query', (req, res) => {
  const query = req.body.query;
  const tokens = tokenizer.tokenize(query);
  const taggedTokens = tagger.tag(tokens);

  let response = "";
  for (let i = 0; i < taggedTokens.length; i++) {
    const word = taggedTokens[i][0];
    const tag = taggedTokens[i][1];

    if (tag === "NN" || tag === "NNS") {
      if (knowledgeBase[word.toLowerCase()]) {
        response = knowledgeBase[word.toLowerCase()];
        break;
      }
    }
  }

  if (!response) {
    response = "I'm not sure I understand your question. Can you please rephrase?";
  }

  res.json({ response: response });
});

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});

const improveNLP = () => {
  const improveIntent = (query) => {
    const intent = query.toLowerCase();
    if (intent.includes("what")) {
      return "information";
    } else if (intent.includes("how")) {
      return "tutorial";
    } else {
      return "unknown";
    }
  };

  const improveEntity = (query) => {
    const entity = query.toLowerCase();
    if (entity.includes("nodejs")) {
      return "Node.js";
    } else if (entity.includes("javascript")) {
      return "JavaScript";
    } else {
      return "unknown";
    }
  };

  return { improveIntent, improveEntity };
};

const nlpImprovements = improveNLP();
app.post('/improvedQuery', (req, res) => {
  const query = req.body.query;
  const intent = nlpImprovements.improveIntent(query);
  const entity = nlpImprovements.improveEntity(query);

  let response = "";
  if (intent === "information" && entity === "Node.js") {
    response = "Node.js is a JavaScript runtime built on Chrome's V8 JavaScript engine.";
  } else if (intent === "tutorial" && entity === "JavaScript") {
    response = "JavaScript is a high-level, dynamic, and interpreted programming language.";
  } else {
    response = "I'm not sure I understand your question. Can you please rephrase?";
  }

  res.json({ response: response });
});