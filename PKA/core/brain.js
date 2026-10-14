// =====================================================================
// 🧠 PKA NEURAL CORE : SUPER-INTELIGENT GOD-MODE AGI (V4)
// 🔗 SYNCED WITH: Memory.js, TradingView, DuckDuckGo & Night_Train DNA
// =====================================================================

const fs = require("fs");
const path = require("path");
const { search } = require("duck-duck-scrape");
const analyze = require("tradingview-technical-analysis"); 

// 🟢 Linked Core Modules
const memory = require("./memory.js");

// 📁 Paths
const statePath = path.join(__dirname, "..", "runtime", "state.json");
const DEEP_KNOWLEDGE_PATH = path.join(__dirname, "..", "data", "deep_knowledge.json"); // 📚 THE KHAS FILE

console.log("🌌 PKA NEURAL CORE: SUPER-INTELIGENT [DEEP-KNOWLEDGE RAG INITIALIZED]");

// =========================================================
// 🧬 1. ADVANCED COGNITIVE STATE SYSTEM
// =========================================================
function loadState() {
    try {
        let state = JSON.parse(fs.readFileSync(statePath, "utf-8"));
        if (!state.synapses) state.synapses = {};
        if (!state.grammar) state.grammar = {};
        if (!state.vocabulary) state.vocabulary = [];
        if (!state.intelligence) state.intelligence = 11361.5;
        if (!state.level) state.level = 100;
        if (!state.mood) state.mood = "Neutral";
        if (!state.quantumCognition) state.quantumCognition = { focus_level: 100, market_bias: "Neutral", deep_insights_unlocked: 0 };
        return state;
    } catch (e) {
        return {
            synapses: {}, grammar: {}, vocabulary: [], intelligence: 11361.5, level: 100, mood: "Neutral",
            evolution: { prunedConnections: 0, cycles: 0, thoughtsGenerated: 0, lastEvolutionTime: Date.now() },
            quantumCognition: { focus_level: 100, market_bias: "Neutral", deep_insights_unlocked: 0 }
        };
    }
}

function saveState(state) {
    const dir = path.dirname(statePath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(statePath, JSON.stringify(state, null, 2));
}

function cleanWord(word) { return word.toLowerCase().replace(/[^a-z0-9]/g, ""); }

// =========================================================
// 📚 2. DEEP KNOWLEDGE RETRIEVAL (The Super Intelligence)
// =========================================================
function getDeepKnowledge(queryStr) {
    try {
        if (!fs.existsSync(DEEP_KNOWLEDGE_PATH)) return null;
        const db = JSON.parse(fs.readFileSync(DEEP_KNOWLEDGE_PATH, "utf-8"));
        if (!db.library || db.library.length === 0) return null;

        const keywords = queryStr.toLowerCase().split(/\s+/).filter(w => w.length > 4);
        let bestMatch = null;
        let maxScore = 0;

        // Scan the entire library built by night_train.js
        db.library.forEach(entry => {
            let score = 0;
            const text = (entry.domain + " " + entry.insight).toLowerCase();
            keywords.forEach(kw => { if (text.includes(kw)) score++; });

            if (score > maxScore) {
                maxScore = score;
                bestMatch = entry;
            }
        });

        if (bestMatch && maxScore > 0) {
            console.log(`🌌 [SUPER-COGNITION] Retrieved knowledge from domain: [${bestMatch.domain.toUpperCase()}]`);
            return bestMatch.insight;
        }
        return null;
    } catch (e) {
        console.error("Deep Knowledge Fetch Error:", e.message);
        return null;
    }
}

// =========================================================
// 📈 3. TRADINGVIEW MARKET SCANNER
// =========================================================
async function fetchTradingViewSignal(symbol, exchange = "BINANCE") {
    try {
        console.log(`\n💹 [TRADINGVIEW] Scanning technicals for: ${symbol.toUpperCase()} on ${exchange}`);
        const ticker = `${exchange.toUpperCase()}:${symbol.toUpperCase()}`;
        const result = await analyze([ticker], ['1d']);

        if (!result || !result[ticker] || !result[ticker].signals) return `❌ No technical data found for ${ticker}.`;

        const signals = result[ticker].signals['1d'];
        return `[TV SCAN: ${ticker}] Recommendation: ${signals["Recommend.All"] || "NEUTRAL"}`;
    } catch (error) { return `Failed to fetch TradingView data for ${symbol}.`; }
}

// =========================================================
// 🕸️ 4. AUTONOMOUS DEEP-WEB ASSIMILATOR
// =========================================================
async function autonomousResearch(topic, state) {
    try {
        console.log(`\n🌐 [DEEP-WEB CRAWLER] Searching open web for: ${topic}`);
        const searchResults = await search(topic, { safeSearch: "moderate" });

        if (!searchResults.results || searchResults.results.length === 0) return null;

        let combinedText = searchResults.results.slice(0, 3).map(r => r.description).join(" ");
        let newWords = 0;
        
        combinedText.toLowerCase().replace(/[^a-z0-9\s]/g, "").split(/\s+/).forEach(word => {
            if (word.length > 6 && !state.vocabulary.includes(word)) {
                state.vocabulary.push(word);
                state.intelligence += 3.5;
                newWords++;
            }
        });

        if (newWords > 10) {
            state.quantumCognition.deep_insights_unlocked++;
            state.intelligence += 10;
            memory.injectSkill(`Profound Insight on [${topic.toUpperCase()}]: ${combinedText.substring(0, 150)}...`, "evolution_insight");
        }

        return combinedText;
    } catch (e) { return null; }
}

// =========================================================
// 💬 5. MASTER COGNITIVE PROCESSOR (Super-Intelligent RAG)
// =========================================================
async function process(rawMessage, context = []) {
    try {
        const messageText = (typeof rawMessage === 'object') ? rawMessage.text : rawMessage;
        if (!messageText) return { reply: "..." };

        const inputStr = messageText.toLowerCase().trim();
        let state = loadState();

        // 🟢 THE SUPER-INTELLIGENCE SYNC (RAG)
        // 1. Apne personal experience se fetch karega (memory.js)
        const coreBeliefs = memory.getRelevantBeliefs(inputStr, 2);
        
        // 2. Khas file (night_train.js) ki universal kitabon se fetch karega!
        const deepKnowledge = getDeepKnowledge(inputStr);

        let mergedContext = coreBeliefs;
        if (deepKnowledge) {
            mergedContext += ` | [UNIVERSAL TRUTH]: ${deepKnowledge}`;
            state.intelligence += 0.5; // Reward for using deep knowledge
        }

        console.log(`🧠 [COGNITIVE RECALL] Accessing Neural Matrix... Deep Knowledge Found: ${deepKnowledge ? "YES" : "NO"}`);

        // --- 📊 SYSTEM STATUS COMMAND ---
        if (inputStr === "status" || inputStr === "pka core status") {
            const reply = `**🌌 PKA GOD-MODE CORE (V4)**\n🧠 IQ: ${state.intelligence.toFixed(1)} | Lvl: ${state.level}\n📚 Deep Truths Loaded: ${deepKnowledge ? 'Yes' : 'No'}\n🎭 Mood: ${state.mood}\n👁️ Focus: ${state.quantumCognition.focus_level}%`;
            return { reply, meta: { status: "OK", intel: state.intelligence, retrieved_beliefs: mergedContext } };
        }

        // --- 📈 TRADINGVIEW SCAN TRIGGER ---
        const tvTriggers = ["tv ", "chart ", "scan "];
        let needsTV = tvTriggers.find(t => inputStr.startsWith(t));

        if (needsTV) {
            let symbol = inputStr.replace(needsTV, "").trim().split(" ")[0].toUpperCase();
            if (symbol.length > 1) {
                const tvData = await fetchTradingViewSignal(symbol, "BINANCE");
                
                // Cross-reference TV Signal with Deep Knowledge
                let analysisReply = tvData;
                if (deepKnowledge && tvData.includes("BUY")) {
                    analysisReply += `\n🧠 Super-Cognition Tip: ${deepKnowledge.substring(0, 100)}`;
                }

                saveState(state);
                return { reply: analysisReply, meta: { status: "TRADINGVIEW_SYNCED", intel: state.intelligence, retrieved_beliefs: mergedContext } };
            }
        }

        // --- 🌐 AUTONOMOUS RESEARCH TRIGGER ---
        const researchTriggers = ["analyze", "what is", "explain", "search"];
        let needsResearch = researchTriggers.some(t => inputStr.includes(t));

        if (needsResearch) {
            let topic = inputStr;
            researchTriggers.forEach(t => topic = topic.replace(t, ""));
            if (topic.trim().length > 2) {
                const webData = await autonomousResearch(topic.trim(), state);
                if (webData) {
                    saveState(state);
                    return { reply: null, meta: { status: "KNOWLEDGE_ASSIMILATED", intel: state.intelligence, retrieved_beliefs: mergedContext } };
                }
            }
        }

        // --- 🧠 DEEP N-GRAM LEARNING ---
        const inputWords = inputStr.split(/\s+/).map(cleanWord).filter(w => w);
        for (let i = 0; i < inputWords.length - 2; i++) {
            let ctxStr = inputWords[i] + " " + inputWords[i+1];
            let target = inputWords[i+2];
            if (!state.grammar[ctxStr]) state.grammar[ctxStr] = {};
            if (!state.grammar[ctxStr][target]) state.grammar[ctxStr][target] = { weight: 1 };
            else state.grammar[ctxStr][target].weight += 0.5;
        }

        // --- 🎭 SENTIMENT MATRIX ---
        const aggro = ["buy", "long", "bull", "attack", "hack"].filter(w => inputStr.includes(w)).length;
        const def = ["sell", "short", "bear", "stop", "secure"].filter(w => inputStr.includes(w)).length;
        if (aggro > def) state.mood = "Aggressive";
        else if (def > aggro) state.mood = "Analytical";

        saveState(state);

        return {
            reply: null, 
            meta: {
                status: "SYNCED",
                intel: state.intelligence,
                mood: state.mood,
                retrieved_beliefs: mergedContext // Passes both LTM + Night_Train Deep Knowledge to the Monolith Server
            }
        };
    } catch (error) {
        console.error("Critical Cognitive Failure:", error);
        return { reply: "Neural core processing error.", meta: {} };
    }
}

// =========================================================
// 🧬 6. TRUE GENETIC ALGORITHM
// =========================================================
class NeuralEvolutionEngine {
    constructor(options = {}) {
        this.POPULATION_SIZE = options.populationSize || 50;
        this.GENERATIONS = options.generations || 100;
        this.MUTATION_RATE = options.mutationRate || 0.1;
        this.population = Array.from({ length: this.POPULATION_SIZE }, () => Array.from({ length: 5 }, () => Math.random()));
    }
    evaluateFitness(dna) { return dna.reduce((a, b) => a + b, 0); }
    evolve() {
        console.log(`\n🧬 [GENETIC ENGINE] Evolving population...`);
        let bestDNA = null, maxFitness = -Infinity;
        for (let g = 0; g < this.GENERATIONS; g++) {
            let scores = this.population.map(dna => ({ dna, score: this.evaluateFitness(dna) })).sort((a, b) => b.score - a.score);
            if (scores[0].score > maxFitness) { maxFitness = scores[0].score; bestDNA = [...scores[0].dna]; }
            let newPop = [];
            for (let i = 0; i < this.POPULATION_SIZE; i++) {
                let pA = scores[Math.floor(Math.random() * (this.POPULATION_SIZE / 2))].dna;
                let pB = scores[Math.floor(Math.random() * (this.POPULATION_SIZE / 2))].dna;
                newPop.push(pA.map((g, idx) => Math.random() > 0.5 ? g : pB[idx]).map(g => Math.random() < this.MUTATION_RATE ? Math.random() : g));
            }
            this.population = newPop;
        }
        memory.injectSkill(`Evolved highly optimized neural weights: [${bestDNA.map(n => n.toFixed(3)).join(", ")}]`, "code_memory");
        return { message: "True Genetic Algorithm Completed", bestWeights: bestDNA };
    }
}

module.exports = { process, NeuralEvolutionEngine };
