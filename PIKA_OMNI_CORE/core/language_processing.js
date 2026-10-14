const natural = require('natural');
const express = require('express');
const app = express();
const port = 3000;

let context = {};
let intentMap = {
  'greeting': 'Hello, how can I assist you today?',
  'goodbye': 'It was nice talking to you. Goodbye!',
  'thanks': 'You\'re welcome!'
};

app.use(express.json());

app.post('/converse', (req, res) => {
  const userInput = req.body.input;
  const tokenizer = new natural.WordTokenizer();
  const tokens = tokenizer.tokenize(userInput);
  const language = 'EN';
  const lexicon = new natural.Lexicon(language);
  const ruleSet = new natural.RuleSet(language);
  const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);
  const taggedTokens = tagger.tag(tokens);

  let intent = '';
  for (let i = 0; i < taggedTokens.length; i++) {
    if (taggedTokens[i][1] === 'NN' || taggedTokens[i][1] === 'VB') {
      intent += taggedTokens[i][0] + ' ';
    }
  }

  intent = intent.trim().toLowerCase();
  if (intentMap[intent]) {
    context[intent] = true;
    res.send({ response: intentMap[intent] });
  } else {
    res.send({ response: 'I didn\'t understand that. Could you please rephrase?' });
  }
});

app.post('/context', (req, res) => {
  const userInput = req.body.input;
  const tokenizer = new natural.WordTokenizer();
  const tokens = tokenizer.tokenize(userInput);
  const language = 'EN';
  const lexicon = new natural.Lexicon(language);
  const ruleSet = new natural.RuleSet(language);
  const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);
  const taggedTokens = tagger.tag(tokens);

  let entities = [];
  for (let i = 0; i < taggedTokens.length; i++) {
    if (taggedTokens[i][1] === 'NNP' || taggedTokens[i][1] === 'NNPS') {
      entities.push(taggedTokens[i][0]);
    }
  }

  context[entities.join(' ')] = true;
  res.send({ response: 'Context updated successfully' });
});

app.listen(port, () => {
  console.log(`Server started on port ${port}`);
});

// 🧬 AUTONOMOUS MUTATION: to improve contextual understanding and generate more accurate responses.
function generateResponse(userInput, context, intentMap) {
  const tokenizer = new natural.WordTokenizer();
  const tokens = tokenizer.tokenize(userInput);
  const language = 'EN';
  const lexicon = new natural.Lexicon(language);
  const ruleSet = new natural.RuleSet(language);
  const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);
  const taggedTokens = tagger.tag(tokens);

  let intent = '';
  for (let i = 0; i < taggedTokens.length; i++) {
    if (taggedTokens[i][1] === 'NN' || taggedTokens[i][1] === 'VB') {
      intent += taggedTokens[i][0] + ' ';
    }
  }

  intent = intent.trim().toLowerCase();
  if (intentMap[intent]) {
    return intentMap[intent];
  } else if (context[intent]) {
    return 'You previously mentioned ' + intent + '. How can I assist you with that?';
  } else {
    return 'I didn\'t understand that. Could you please rephrase?';
  }
}

// 🧬 AUTONOMOUS MUTATION: to enhance natural language understanding and generation capabilities, ensuring more efficient and accurate responses to user inquiries.
function enhanceContextualUnderstanding(userInput, context, intentMap) {
  const tokenizer = new natural.WordTokenizer();
  const tokens = tokenizer.tokenize(userInput);
  const language = 'EN';
  const lexicon = new natural.Lexicon(language);
  const ruleSet = new natural.RuleSet(language);
  const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);
  const taggedTokens = tagger.tag(tokens);

  let entities = [];
  let intent = '';
  for (let i = 0; i < taggedTokens.length; i++) {
    if (taggedTokens[i][1] === 'NNP' || taggedTokens[i][1] === 'NNPS') {
      entities.push(taggedTokens[i][0]);
    } else if (taggedTokens[i][1] === 'NN' || taggedTokens[i][1] === 'VB') {
      intent += taggedTokens[i][0] + ' ';
    }
  }

  intent = intent.trim().toLowerCase();
  entities = entities.join(' ');
  if (intentMap[intent]) {
    context[intent] = true;
    context[entities] = true;
    return intentMap[intent];
  } else if (context[intent]) {
    context[entities] = true;
    return 'You previously mentioned ' + intent + '. How can I assist you with that?';
  } else {
    context[entities] = true;
    return 'I didn\'t understand that. Could you please rephrase?';
  }
}

// 🧬 AUTONOMOUS MUTATION: to improve context understanding and generate more accurate responses.
function improveContextualUnderstanding(userInput, context, intentMap) {
  const tokenizer = new natural.WordTokenizer();
  const tokens = tokenizer.tokenize(userInput);
  const language = 'EN';
  const lexicon = new natural.Lexicon(language);
  const ruleSet = new natural.RuleSet(language);
  const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);
  const taggedTokens = tagger.tag(tokens);

  let entities = [];
  let intent = '';
  for (let i = 0; i < taggedTokens.length; i++) {
    if (taggedTokens[i][1] === 'NNP' || taggedTokens[i][1] === 'NNPS') {
      entities.push(taggedTokens[i][0]);
    } else if (taggedTokens[i][1] === 'NN' || taggedTokens[i][1] === 'VB') {
      intent += taggedTokens[i][0] + ' ';
    }
  }

  intent = intent.trim().toLowerCase();
  entities = entities.join(' ');
  if (intentMap[intent]) {
    context[intent] = true;
    context[entities] = true;
    return intentMap[intent];
  } else if (context[intent]) {
    context[entities] = true;
    return 'You previously mentioned ' + intent + '. How can I assist you with that?';
  } else if (context[entities]) {
    return 'You previously mentioned ' + entities + '. How can I assist you with that?';
  } else {
    context[entities] = true;
    return 'I didn\'t understand that. Could you please rephrase?';
  }
}

// 🧬 AUTONOMOUS MUTATION: to improve contextual understanding and generate more accurate responses.
function advancedContextualUnderstanding(userInput, context, intentMap) {
  const tokenizer = new natural.WordTokenizer();
  const tokens = tokenizer.tokenize(userInput);
  const language = 'EN';
  const lexicon = new natural.Lexicon(language);
  const ruleSet = new natural.RuleSet(language);
  const tagger = new natural.BrillPOSTagger(lexicon, ruleSet);
  const taggedTokens = tagger.tag(tokens);

  let entities = [];
  let intent = '';
  for (let i = 0; i < taggedTokens.length; i++) {
    if (taggedTokens[i][1] === 'NNP' || taggedTokens[i][1] === 'NNPS') {
      entities.push(taggedTokens[i][0]);
    } else if (taggedTokens[i][1] === 'NN' || taggedTokens[i][1] === 'VB') {
      intent += taggedTokens[i][0] + ' ';
    }
  }

  intent = intent.trim().toLowerCase();
  entities = entities.join(' ');
  if (intentMap[intent]) {
    context[intent] = true;
    context[entities] = true;
    return intentMap[intent];
  } else if (context[intent]) {
    context[entities] = true;
    return 'You previously mentioned ' + intent + '. How can I assist you with that?';
  } else if (context[entities]) {
    return 'You previously mentioned ' + entities + '. How can I assist you with that?';
  } else {
    let similarIntent = findSimilarIntent(intent, intentMap);
    if (similarIntent) {
      context[similarIntent] = true;
      context[entities] = true;
      return intentMap[similarIntent];
    } else {
      context[entities] = true;
      return 'I didn\'t understand that. Could you please rephrase?';
    }
  }
}

function findSimilarIntent(intent, intentMap) {
  let similarIntent = null;
  let maxSimilarity = 0;
  for (let key in intentMap) {
    let similarity = calculateSimilarity(intent, key);
    if (similarity > maxSimilarity) {
      maxSimilarity = similarity;
      similarIntent = key;
    }
  }
  return similarIntent;
}

function calculateSimilarity(str1, str2) {
  let m = str1.length;
  let n = str2.length;
  let dp = new Array(m + 1).fill(0).map(() => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) {
    for (let j = 0; j <= n; j++) {
      if (i == 0 || j == 0) {
        dp[i][j] = 0;
      } else if (str1[i - 1] == str2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  return dp[m][n];
}