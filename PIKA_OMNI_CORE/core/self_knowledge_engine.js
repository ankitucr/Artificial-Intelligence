// ══════════════════════════════════════════════════════════════════════════
// 🧠 SELF-KNOWLEDGE ENGINE — Pika tries its OWN learned brain first.
// Only falls back to Groq/Samba (router.js universalInference) when local
// confidence is too low. This is what makes Pika self-dependent instead of
// hitting APIs for every single message.
// ══════════════════════════════════════════════════════════════════════════

const fs = require('fs-extra');
const path = require('path');

const DATA_DIR       = path.join(__dirname, '../data');
const DEEP_KNOWLEDGE  = path.join(DATA_DIR, 'deep_knowledge.json');
const SEMANTIC_CONFIG = path.join(DATA_DIR, 'semantic_config.json');

// How confident Pika must be in its own knowledge before it trusts itself
// instead of asking an LLM. Tune this: higher = more API calls, safer answers.
// Lower = fewer API calls, but risk of shallow/wrong local answers.
const CONFIDENCE_THRESHOLD = 0.75;
const MIN_CONCEPT_MATCHES  = 1; // at least this many known concepts must appear

// ==========================================
// 🔍 Extract candidate "concepts" from a raw user message
// ==========================================
function extractCandidateWords(text) {
    return text
        .toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .split(/\s+/)
        .filter(w => w.length > 2);
}

// ==========================================
// 🧠 Check how confident Pika's own semantic memory is about this query
// ==========================================
async function checkOwnConfidence(userMessage) {
    let config = {};
    try {
        config = await fs.readJson(SEMANTIC_CONFIG);
    } catch (e) {
        return { confident: false, avgConfidence: 0, matchedConcepts: [] };
    }

    const words = extractCandidateWords(userMessage);
    const techCore = config.tech_core || {};
    const actionCore = config.action || {};

    const matchedConcepts = [];
    let totalConfidence = 0;

    for (const word of words) {
        if (techCore[word]) {
            matchedConcepts.push({ word, confidence: techCore[word].confidence, type: 'tech' });
            totalConfidence += techCore[word].confidence;
        } else if (actionCore[word]) {
            matchedConcepts.push({ word, confidence: actionCore[word].confidence, type: 'action' });
            totalConfidence += actionCore[word].confidence;
        }
    }

    if (matchedConcepts.length < MIN_CONCEPT_MATCHES) {
        return { confident: false, avgConfidence: 0, matchedConcepts };
    }

    const avgConfidence = totalConfidence / matchedConcepts.length;
    return {
        confident: avgConfidence >= CONFIDENCE_THRESHOLD,
        avgConfidence,
        matchedConcepts
    };
}

// ==========================================
// 📚 Try to build an answer purely from deep_knowledge.json
// ==========================================
async function tryLocalAnswer(userMessage) {
    let deepK = {};
    try {
        deepK = await fs.readJson(DEEP_KNOWLEDGE);
    } catch (e) {
        return null;
    }

    const words = extractCandidateWords(userMessage);
    const knownTopics = Object.keys(deepK);

    const matchedTopic = knownTopics.find(topic =>
        words.some(w => topic.toLowerCase().includes(w) || w.includes(topic.toLowerCase()))
    );

    if (!matchedTopic) return null;

    const entry = deepK[matchedTopic];
    if (!entry || !entry.definition) return null;

    let answer = `${entry.definition}`;
    if (entry.core_concepts && entry.core_concepts.length) {
        answer += `\n\nRelated concepts: ${entry.core_concepts.join(', ')}`;
    }
    if (entry.use_case) {
        answer += `\n\nUse case: ${entry.use_case}`;
    }

    return { answer, topic: matchedTopic, learnedOn: entry.learned_on };
}

// ══════════════════════════════════════════════════════════════════════════
// 🎯 MAIN ENTRY POINT
// Returns { source: 'self' | 'fallback', reply, meta }
// ══════════════════════════════════════════════════════════════════════════
async function resolveWithSelfKnowledge(userMessage) {
    const confidenceCheck = await checkOwnConfidence(userMessage);
    const localAnswer = await tryLocalAnswer(userMessage);

    if (confidenceCheck.confident && localAnswer) {
        return {
            source: 'self',
            reply: localAnswer.answer,
            meta: {
                topic: localAnswer.topic,
                confidence: confidenceCheck.avgConfidence,
                matchedConcepts: confidenceCheck.matchedConcepts.map(c => c.word),
                learnedOn: localAnswer.learnedOn
            }
        };
    }

    return {
        source: 'fallback',
        reply: null,
        meta: {
            reason: !localAnswer ? 'no_local_knowledge' : 'low_confidence',
            confidence: confidenceCheck.avgConfidence
        }
    };
}

module.exports = { resolveWithSelfKnowledge, checkOwnConfidence, tryLocalAnswer };
