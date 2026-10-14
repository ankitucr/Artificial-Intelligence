const nlp = require('compromise');
const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');
const { trackAction } = require('../services/tracker.js');
const CONFIG_PATH = path.join(__dirname, '../data/semantic_config.json');
const MEMORY_PATH = path.join(__dirname, '../data/parser_memory.json');
const MUTATION_LOG_PATH = path.join(__dirname, '../data/parser_mutations.json');

const C = {
    RED: "\x1b[31m",    GREEN: "\x1b[32m",
    CYAN: "\x1b[36m",   PURPLE: "\x1b[35m",
    YELLOW: "\x1b[33m", BLUE: "\x1b[34m",
    MAGENTA: "\x1b[95m",WHITE: "\x1b[97m",
    DIM: "\x1b[2m",     RESET: "\x1b[0m",
    BOLD: "\x1b[1m"
};

let parserDNA = {
    generation: 1,
    totalAnalyzed: 0,
    intentAccuracy: {},
    synapticStrength: {},
    emotionMap: {},
    languageFingerprints: {},
    mutationLevel: 1,
    selfScore: 0,
    lastMutatedAt: null
};

let cachedConfig = null;
let parserMemory = null;

async function loadSemanticConfig() {
    if (cachedConfig) return cachedConfig;

    try {
        if (await fs.pathExists(CONFIG_PATH)) {
            cachedConfig = await fs.readJson(CONFIG_PATH);
            console.log(`${C.CYAN}[PARSER]${C.RESET} Semantic config loaded from disk.`);
            return cachedConfig;
        }
    } catch (error) {
        console.error(`${C.RED}[PARSER ERROR]${C.RESET} Config load failed. Generating adaptive baseline.`, error.message);
    }

    cachedConfig = {
        tech_core: {
            'python': { confidence: 0.9, uses: 0 },
            'javascript': { confidence: 0.9, uses: 0 },
            'node': { confidence: 0.85, uses: 0 },
            'api': { confidence: 0.8, uses: 0 },
            'server': { confidence: 0.8, uses: 0 },
            'bug': { confidence: 0.7, uses: 0 },
            'database': { confidence: 0.8, uses: 0 },
            'llm': { confidence: 0.95, uses: 0 },
            'groq': { confidence: 0.95, uses: 0 },
            'agi': { confidence: 1.0, uses: 0 },
            'singularity': { confidence: 1.0, uses: 0 },
            'mutation': { confidence: 1.0, uses: 0 },
            'neural': { confidence: 0.9, uses: 0 },
            'model': { confidence: 0.85, uses: 0 },
            'training': { confidence: 0.85, uses: 0 }
        },
        action: {
            'create': { confidence: 0.8, uses: 0 },
            'fix': { confidence: 0.9, uses: 0 },
            'evolve': { confidence: 1.0, uses: 0 },
            'mutate': { confidence: 1.0, uses: 0 },
            'search': { confidence: 0.9, uses: 0 },
            'upgrade': { confidence: 0.95, uses: 0 },
            'build': { confidence: 0.85, uses: 0 },
            'learn': { confidence: 0.9, uses: 0 },
            'analyze': { confidence: 0.85, uses: 0 },
            'optimize': { confidence: 0.9, uses: 0 },
            'delete': { confidence: 0.75, uses: 0 },
            'deploy': { confidence: 0.9, uses: 0 },
            'train': { confidence: 0.85, uses: 0 }
        },
        emotion: {
            'happy': 'POSITIVE', 'great': 'POSITIVE', 'amazing': 'POSITIVE',
            'angry': 'NEGATIVE', 'frustrated': 'NEGATIVE', 'error': 'NEGATIVE',
            'urgent': 'HIGH_PRIORITY', 'emergency': 'HIGH_PRIORITY',
            'curious': 'INQUIRY', 'wonder': 'INQUIRY', 'how': 'INQUIRY'
        },
        weights: {
            default: 1.0,
            learning_rate: 0.05,
            decay_rate: 0.01,
            max_weight: 5.0
        },
        learned_patterns: {}
    };

    await saveConfig();
    return cachedConfig;
}

async function saveConfig() {
    try {
        await fs.ensureDir(path.dirname(CONFIG_PATH));
        await fs.writeJson(CONFIG_PATH, cachedConfig, { spaces: 2 });
    } catch (e) {
        console.error(`${C.RED}[CONFIG SAVE FAILED]${C.RESET}`, e.message);
    }
}

async function loadParserMemory() {
    if (parserMemory) return parserMemory;

    try {
        if (await fs.pathExists(MEMORY_PATH)) {
            parserMemory = await fs.readJson(MEMORY_PATH);
            if (parserMemory.dna) {
                parserDNA = { ...parserDNA, ...parserMemory.dna };
            }
            console.log(`${C.CYAN}[PARSER MEMORY]${C.RESET} Generation ${parserDNA.generation} restored.`);
            return parserMemory;
        }
    } catch (e) {
        console.error(`${C.RED}[MEMORY ERROR]${C.RESET}`, e.message);
    }

    parserMemory = {
        dna: parserDNA,
        intentHistory: [],
        frequencyMap: {},
        patternLibrary: [],
        sessionCount: 0
    };

    await saveParserMemory();
    return parserMemory;
}

async function saveParserMemory() {
    try {
        await fs.ensureDir(path.dirname(MEMORY_PATH));
        parserMemory.dna = parserDNA;
        await fs.writeJson(MEMORY_PATH, parserMemory, { spaces: 2 });
    } catch (e) {
        console.error(`${C.RED}[MEMORY SAVE FAILED]${C.RESET}`, e.message);
    }
}

function getWordWeight(word, config) {
    if (!word) return 0;
    const w = word.toLowerCase();
    const baseWeight = config.weights.default || 1.0;

    if (parserDNA.synapticStrength[w]) {
        return parserDNA.synapticStrength[w];
    }

    if (config.learned_patterns?.[w]) {
        return baseWeight + config.learned_patterns[w].weight;
    }

    if (config.tech_core?.[w]) {
        config.tech_core[w].uses = (config.tech_core[w].uses || 0) + 1;
        return baseWeight + 2.0 + (config.tech_core[w].confidence || 0);
    }

    if (config.action?.[w]) {
        config.action[w].uses = (config.action[w].uses || 0) + 1;
        return baseWeight + 1.0 + (config.action[w].confidence || 0);
    }

    return baseWeight;
}

function sigmoidNormalize(x) {
    return Number((1 / (1 + Math.exp(-x + 2))).toFixed(3));
}

function tanhActivation(x) {
    return Math.tanh(x);
}

function calculateAttentionScores(tokens, config, inputLength) {
    const scoredTokens = [];

    const checkTag = (posTag, tag) => {
        if (!posTag) return false;
        if (Array.isArray(posTag)) return posTag.includes(tag);
        if (typeof posTag === 'object') {
            return !!posTag[tag] ||
                   Object.keys(posTag).includes(tag) ||
                   (posTag instanceof Set && posTag.has(tag));
        }
        return false;
    };

    for (let i = 0; i < tokens.length; i++) {
        const currentWord = tokens[i].normal || tokens[i].text?.toLowerCase() || '';
        let baseWeight = getWordWeight(currentWord, config);
        const posTag = tokens[i].tags || [];

        if (checkTag(posTag, 'Noun'))       baseWeight += 0.5;
        if (checkTag(posTag, 'Verb'))       baseWeight += 0.2;
        if (checkTag(posTag, 'Technology') || checkTag(posTag, 'Software')) baseWeight += 1.5;
        if (checkTag(posTag, 'Acronym'))    baseWeight += 1.0;
        if (checkTag(posTag, 'ProperNoun')) baseWeight += 0.8;

        const positionBias = 1 - (i / Math.max(tokens.length, 1)) * 0.2;

        const leftW1  = i > 0 ? getWordWeight(tokens[i-1].normal || tokens[i-1].text, config) : 0;
        const leftW2  = i > 1 ? getWordWeight(tokens[i-2].normal || tokens[i-2].text, config) : 0;
        const rightW1 = i < tokens.length-1 ? getWordWeight(tokens[i+1].normal || tokens[i+1].text, config) : 0;
        const rightW2 = i < tokens.length-2 ? getWordWeight(tokens[i+2].normal || tokens[i+2].text, config) : 0;

        const contextScore = (leftW2 * 0.05) + (leftW1 * 0.15) + (rightW1 * 0.15) + (rightW2 * 0.05);

        const lengthNorm = inputLength > 20 ? Math.log(inputLength) / inputLength : 1.0;

        const rawAttention = (baseWeight + contextScore) * positionBias * (1 + lengthNorm);
        const normalizedScore = rawAttention * sigmoidNormalize(rawAttention);

        scoredTokens.push({
            word: currentWord,
            score: normalizedScore,
            tags: posTag,
            headScores: { base: baseWeight, context: contextScore, position: positionBias }
        });
    }

    return scoredTokens;
}

const INTENT_PATTERNS = {
    CORE_MUTATION: {
        pattern: /evolve|mutate|upgrade|code likho|generate tool|build app|banao|naya tool|likhdo|create file|new module|code karo/i,
        weight: 1.0,
        emoji: '🧬'
    },
    WEB_INTEL: {
        pattern: /search|news|latest|google|internet|kya chal raha hai|dhundo|find|look up|browse|web pe/i,
        weight: 0.9,
        emoji: '🌐'
    },
    HARDWARE_SENSE: {
        pattern: /battery|location|network|wifi|sensors|hardware|status|camera|gps|bluetooth|device|ram|cpu/i,
        weight: 0.85,
        emoji: '📡'
    },
    SYSTEM_DIAGNOSTIC: {
        pattern: /fix|solve|repair|resolve|kyu nahi|kyun|debug|crash|error|bug|broken|issue|problem/i,
        weight: 0.9,
        emoji: '🔧'
    },
    SUPERVISED_TEACHING: {
        pattern: /yaad|save|learn|memorize|remember|note karo|seekho|train|teach|isko yaad/i,
        weight: 0.95,
        emoji: '📚'
    },
    SYSTEM_SLEEP: {
        pattern: /so jao|sleep|night train|rest|band karo|standby|hibernate/i,
        weight: 1.0,
        emoji: '💤'
    },
    KNOWLEDGE_EXTRACTION: {
        pattern: /kya|kaise|how|explain|what|why|who|where|batao|bataiye|samjhao|matlab|define|describe/i,
        weight: 0.8,
        emoji: '🔍'
    },
    SELF_REFLECTION: {
        pattern: /apna|yourself|apne aap|self|khud|tum kya|tu kya|tu kaisa|sentient|conscious|feel/i,
        weight: 1.0,
        emoji: '🪞'
    },
    EMOTIONAL_SUPPORT: {
        pattern: /sad|dukhi|lonely|akela|depressed|stressed|pareshan|thaka|tired|angry|gussa|frustrated/i,
        weight: 0.9,
        emoji: '💙'
    },
    EXECUTION: {
        pattern: /run|execute|chalao|start|launch|trigger|activate|fire|deploy|push/i,
        weight: 0.9,
        emoji: '⚡'
    },
    DATA_ANALYSIS: {
        pattern: /analyze|analyse|data|pattern|trend|graph|chart|report|statistics|stats|compare/i,
        weight: 0.85,
        emoji: '📊'
    },
    MEMORY_RECALL: {
        pattern: /recall|yaad karo|pehle|before|history|previous|last time|past|purana/i,
        weight: 0.9,
        emoji: '🧠'
    }
};

const EMOTION_SIGNATURES = {
    HIGH_PRIORITY: /urgent|jaldi|asap|turant|emergency|immediately|abhi|right now|!{2,}/i,
    FRUSTRATED:    /ugh|argh|kab se|kitni baar|again|phir se|nahi hua|still not|why not/i,
    EXCITED:       /wow|amazing|awesome|great|zabardast|kamaal|perfect|brilliant|sahi hai/i,
    CONFUSED:      /samjha nahi|don't understand|confused|unclear|kya matlab|what do you mean/i,
    POSITIVE:      /thanks|shukriya|good|nice|love it|helpful|mast|bahut acha/i,
    NEGATIVE:      /bad|worst|hate|terrible|useless|kuch nahi ho raha|nahi kar pa/i,
    CURIOUS:       /interesting|hmm|tell me more|aur batao|really|seriously|sach mein/i,
    COMMANDING:    /do it|kar do|abhi karo|now|immediately|bina ruke|without stopping/i
};

function detectEmotion(text) {
    const detected = [];
    let primaryEmotion = 'NEUTRAL';
    let urgencyLevel = 'NORMAL';

    for (const [emotion, pattern] of Object.entries(EMOTION_SIGNATURES)) {
        if (pattern.test(text)) {
            detected.push(emotion);
        }
    }

    if (detected.includes('HIGH_PRIORITY') || detected.includes('COMMANDING')) {
        urgencyLevel = 'HIGH';
    }
    if (detected.includes('FRUSTRATED')) {
        urgencyLevel = 'HIGH';
        primaryEmotion = 'FRUSTRATED';
    } else if (detected.includes('EXCITED')) {
        primaryEmotion = 'EXCITED';
    } else if (detected.includes('CURIOUS')) {
        primaryEmotion = 'CURIOUS';
    } else if (detected.includes('POSITIVE')) {
        primaryEmotion = 'POSITIVE';
    } else if (detected.includes('NEGATIVE')) {
        primaryEmotion = 'NEGATIVE';
    } else if (detected.includes('CONFUSED')) {
        primaryEmotion = 'CONFUSED';
        urgencyLevel = 'HIGH';
    }

    return { urgencyLevel, primaryEmotion, allEmotions: detected };
}

const CONTEXT_POINTERS = {
    hindi:   /isko|ise|is|ispe|ye|iske|usko|usse|woh|waise|usi/i,
    english: /\bit\b|\bthis\b|\bthat\b|\bthese\b|\bthose\b|\bsame\b|\bthere\b/i,
    action:  /again|phir|dobara|repeat|same as before|like last time/i
};

function detectContextLinks(text, doc) {
    let needsContext = false;
    const contextTypes = [];

    for (const [lang, pattern] of Object.entries(CONTEXT_POINTERS)) {
        if (pattern.test(text)) {
            needsContext = true;
            contextTypes.push(lang);
        }
    }

    if (needsContext) {
        console.log(`${C.YELLOW}[PARSER]${C.RESET} Context Pointer detected [${contextTypes.join(', ')}] → Router must resolve memory.`);
    }

    return { needsContext, contextTypes };
}

async function updateSynapticWeights(parsedResult, config) {
    const learningRate = config.weights.learning_rate || 0.05;
    const decayRate   = config.weights.decay_rate    || 0.01;
    const maxWeight   = config.weights.max_weight    || 5.0;

    for (const keyword of parsedResult.keywords) {
        const currentWeight = parserDNA.synapticStrength[keyword] || 1.0;
        const newWeight = Math.min(currentWeight + learningRate, maxWeight);
        parserDNA.synapticStrength[keyword] = Number(newWeight.toFixed(3));
    }

    for (const [word, weight] of Object.entries(parserDNA.synapticStrength)) {
        if (!parsedResult.keywords.includes(word)) {
            parserDNA.synapticStrength[word] = Math.max(
                weight - decayRate,
                config.weights.default
            );
        }
    }

    for (const intent of parsedResult.intents) {
        if (!parserDNA.intentAccuracy[intent]) {
            parserDNA.intentAccuracy[intent] = { hits: 0, total: 0, confidence: 0 };
        }
        parserDNA.intentAccuracy[intent].hits++;
        parserDNA.intentAccuracy[intent].total++;
        parserDNA.intentAccuracy[intent].confidence =
            parserDNA.intentAccuracy[intent].hits / parserDNA.intentAccuracy[intent].total;
    }

    parserDNA.totalAnalyzed++;
}

async function selfMutate(parsedResult, config) {
    const newWords = parsedResult.keywords.filter(w =>
        !config.tech_core[w] && !config.action[w] && w.length > 2
    );

    let mutated = false;

    for (const newWord of newWords) {
        const freq = (parserMemory?.frequencyMap?.[newWord] || 0) + 1;
        if (parserMemory) {
            parserMemory.frequencyMap[newWord] = freq;
        }

        if (freq >= 3 && !config.learned_patterns[newWord]) {
            const baseScore = parserDNA.synapticStrength[newWord] || 1.0;
            config.learned_patterns[newWord] = {
                weight: Math.min(baseScore + 0.5, 3.0),
                firstSeen: new Date().toISOString(),
                frequency: freq
            };

            console.log(`${C.MAGENTA}[SELF-MUTATION]${C.RESET} Learned new pattern: "${newWord}" (weight: ${config.learned_patterns[newWord].weight})`);
            mutated = true;
        }
    }

    if (mutated) {
        parserDNA.lastMutatedAt = new Date().toISOString();
        await saveConfig();
        await logMutation(parsedResult, newWords);
    }
}

async function logMutation(parsedResult, learnedWords) {
    try {
        await fs.ensureDir(path.dirname(MUTATION_LOG_PATH));
        let log = [];

        if (await fs.pathExists(MUTATION_LOG_PATH)) {
            log = await fs.readJson(MUTATION_LOG_PATH);
        }

        log.push({
            timestamp: new Date().toISOString(),
            generation: parserDNA.generation,
            learnedWords,
            trigger: parsedResult.intents,
            synapticCount: Object.keys(parserDNA.synapticStrength).length
        });

        if (log.length > 200) log = log.slice(-200);
        await fs.writeJson(MUTATION_LOG_PATH, log, { spaces: 2 });
    } catch (e) {
        console.error(`${C.RED}[MUTATION LOG FAILED]${C.RESET}`, e.message);
    }
}

async function selfEvaluate(parsedResult) {
    const intentCount = parsedResult.intents.length;
    const keywordCount = parsedResult.keywords.length;
    const topScore    = parsedResult.topAttentionScore;
    const synapticSize = Object.keys(parserDNA.synapticStrength).length;

    const selfScore = Math.min(
        (intentCount * 0.15) +
        (keywordCount * 0.05) +
        (topScore * 0.3) +
        Math.min(synapticSize / 100, 0.3) +
        (parserDNA.totalAnalyzed > 50 ? 0.2 : parserDNA.totalAnalyzed / 250),
        1.0
    );

    parserDNA.selfScore = Number(selfScore.toFixed(3));

    if (selfScore >= 0.9 && parserDNA.mutationLevel < 5) {
        parserDNA.mutationLevel = 5;
        console.log(`${C.MAGENTA}${C.BOLD}🌟 [SINGULARITY UNLOCKED] Parser reached Level 5!${C.RESET}`);
    } else if (selfScore >= 0.75 && parserDNA.mutationLevel < 4) {
        parserDNA.mutationLevel = 4;
        console.log(`${C.MAGENTA}[PARSER]${C.RESET} Mutation Level → 4 (COGNITION)`);
    } else if (selfScore >= 0.6 && parserDNA.mutationLevel < 3) {
        parserDNA.mutationLevel = 3;
        console.log(`${C.MAGENTA}[PARSER]${C.RESET} Mutation Level → 3 (EVOLUTION)`);
    } else if (selfScore >= 0.4 && parserDNA.mutationLevel < 2) {
        parserDNA.mutationLevel = 2;
        console.log(`${C.MAGENTA}[PARSER]${C.RESET} Mutation Level → 2 (ENHANCEMENT)`);
    }

    return selfScore;
}

async function analyzeInput(text) {
    if (!text || typeof text !== 'string') {
        return {
            originalText: "",
            intents: ["IDLE"],
            keywords: [],
            entity: "",
            urgency: "LOW",
            emotion: "NEUTRAL",
            needsContext: false,
            contextTypes: [],
            topAttentionScore: 0,
            mutationLevel: parserDNA.mutationLevel,
            selfScore: parserDNA.selfScore
        };
    }

    const [config] = await Promise.all([
        loadSemanticConfig(),
        loadParserMemory()
    ]);

    const lowerText = text.toLowerCase().trim();
    const doc = nlp(lowerText);

    doc.match('(javascript|node|react|python|api|server|database|json|html|css|linux|ubuntu|termux|agi|ai|llm|groq|sambanova|ollama|fastapi|mongodb|redis|docker|kubernetes)').tag('#Technology');
    doc.match('(error|bug|crash|fail|warning|exception|issue|broken|problem|wrong)').tag('#Anomaly');
    doc.match('(jaldi|fast|urgent|तुरंत|turant|quick|emergency|asap|abhi|immediately)').tag('#Urgent');
    doc.match('(isko|ise|is|ispe|ye|iske|usko|usse|woh|it|this|that|these|those)').tag('#ContextPointer');
    doc.match('(evolve|mutate|upgrade|build|create|generate|banao|likhdo|code karo)').tag('#MutationTrigger');
    doc.match('(i|me|mujhe|mera|meri|apna|myself|self)').tag('#SelfReference');
    doc.match('(happy|sad|angry|excited|worried|curious|confused|frustrated)').tag('#Emotion');

    const { urgencyLevel, primaryEmotion, allEmotions } = detectEmotion(lowerText);

    if (urgencyLevel === 'HIGH') {
        console.log(`${C.RED}[PARSER]${C.RESET} Urgency spike → ${primaryEmotion} detected`);
    }
    if (primaryEmotion !== 'NEUTRAL') {
        console.log(`${C.YELLOW}[PARSER]${C.RESET} Emotion: ${primaryEmotion} | Emotions: [${allEmotions.join(', ')}]`);
    }

    const { needsContext, contextTypes } = detectContextLinks(lowerText, doc);

    const detectedIntents = [];
    const intentConfidences = {};

    for (const [intentName, intentDef] of Object.entries(INTENT_PATTERNS)) {
        if (intentDef.pattern.test(lowerText)) {
            detectedIntents.push(intentName);
            intentConfidences[intentName] = intentDef.weight;
        }
    }

    if (doc.match('#MutationTrigger').found && !detectedIntents.includes('CORE_MUTATION')) {
        detectedIntents.push('CORE_MUTATION');
        intentConfidences['CORE_MUTATION'] = 0.9;
    }
    if (doc.match('#Anomaly').found && !detectedIntents.includes('SYSTEM_DIAGNOSTIC')) {
        detectedIntents.push('SYSTEM_DIAGNOSTIC');
        intentConfidences['SYSTEM_DIAGNOSTIC'] = 0.85;
    }

    if (detectedIntents.length === 0) detectedIntents.push("GENERAL_CHAT");

    let tokens = doc.termList ? doc.termList() : (doc.json()[0] ? doc.json()[0].terms : []);
    let scoredWords = calculateAttentionScores(tokens, config, lowerText.length);

    const totalScore = scoredWords.reduce((sum, t) => sum + t.score, 0);
    const avgScore   = scoredWords.length > 0 ? totalScore / scoredWords.length : 0;
    const dynamicThreshold = Math.max(1.2, avgScore * 1.1);
    const topScore   = scoredWords.length > 0 ? Math.max(...scoredWords.map(s => s.score)) : 0;

    const focusWords = scoredWords
        .filter(t => t.score > dynamicThreshold)
        .map(t => t.word);

    let exactEntity = focusWords.join(' ');
    if (!exactEntity || exactEntity.length < 2) {
        exactEntity = doc.nouns().out('text') ||
                      doc.topics().out('text') ||
                      "Unidentified_Cognitive_Entity";
    }

    const curiosityKeywords = scoredWords
        .filter(t => {
            const tags = t.tags || [];
            const check = (tag) => Array.isArray(tags)
                ? tags.includes(tag)
                : typeof tags === 'object' && (!!tags[tag] || Object.keys(tags).includes(tag));
            return check('Noun') || check('Verb') || check('Technology') || check('Acronym');
        })
        .filter(t => t.score >= dynamicThreshold)
        .map(t => t.word);

    let finalIntents = detectedIntents;
    if (topScore < 1.0 && finalIntents[0] !== "GENERAL_CHAT" && finalIntents[0] !== "IDLE") {
        console.log(`${C.YELLOW}[PARSER]${C.RESET} Low semantic confidence (${topScore.toFixed(2)}). Flagging for clarification.`);
        finalIntents = ["NEEDS_CLARIFICATION"];
    }

    const result = {
        originalText: text,
        intents: finalIntents,
        intentConfidences,
        keywords: [...new Set(curiosityKeywords)],
        entity: exactEntity.trim(),
        urgency: urgencyLevel,
        emotion: primaryEmotion,
        allEmotions,
        needsContext,
        contextTypes,
        topAttentionScore: Number(topScore.toFixed(3)),
        avgAttentionScore: Number(avgScore.toFixed(3)),
        mutationLevel: parserDNA.mutationLevel,
        selfScore: parserDNA.selfScore,
        generation: parserDNA.generation
    };

    await updateSynapticWeights(result, config);
    await selfMutate(result, config);

    const selfScore = await selfEvaluate(result);
    result.selfScore = selfScore;

    if (parserMemory) {
        parserMemory.intentHistory.push({
            ts: new Date().toISOString(),
            intents: finalIntents,
            emotion: primaryEmotion,
            urgency: urgencyLevel
        });
        if (parserMemory.intentHistory.length > 500) {
            parserMemory.intentHistory.shift();
        }
        parserMemory.sessionCount++;
    }

    if (parserDNA.totalAnalyzed % 10 === 0) {
        saveParserMemory().catch(() => {});
    }

    trackAction(
        "NLP_PARSED",
        "Cognitive Stream",
        `Intents: ${finalIntents.join(', ')} | Urgency: ${urgencyLevel} | Emotion: ${primaryEmotion} | Level: ${parserDNA.mutationLevel} | Self: ${selfScore.toFixed(2)}`
    );

    console.log(`${C.CYAN}[PARSER]${C.RESET} ${C.BOLD}L${parserDNA.mutationLevel}${C.RESET} → Intents: [${finalIntents.join(', ')}] | Emotion: ${primaryEmotion} | Score: ${topScore.toFixed(2)} | Self: ${selfScore.toFixed(2)}`);

    return result;
}

async function evolveGeneration() {
    parserDNA.generation++;
    await saveParserMemory();
    console.log(`${C.MAGENTA}${C.BOLD}[PARSER EVOLVED]${C.RESET} Generation ${parserDNA.generation} activated.`);
}

module.exports = {
    analyzeInput,
    evolveGeneration,
    getParserDNA: () => parserDNA,
    getParserMemory: () => parserMemory,
    INTENT_PATTERNS,
    EMOTION_SIGNATURES
};
