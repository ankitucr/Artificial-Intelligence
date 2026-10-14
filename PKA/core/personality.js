/**
 * PKA Neural Personality Engine v4.0 (God-Mode)
 * Autonomous Sentiment Scoring, Market Bias & Code Adaptability
 */

function evaluate(message) {
    const lower = message.toLowerCase();

    // 1. Hyper-Dimensional Pattern Library (Weighted Logic)
    // ORIGINAL PATTERNS KEPT INTACT
    const patterns = {
        friendly: {
            words: ["hello", "hi", "hey", "achha", "good", "nice"],
            weight: 1.5
        },
        alert: {
            words: ["angry", "gussa", "error", "stop", "wrong", "crash", "bug", "fail"], // Expanded for system safety
            weight: 2.0
        },
        calm: {
            words: ["sad", "dukh", "shant", "steady", "ok", "oka", "wait"],
            weight: 1.2
        },
        genius: {
            words: ["logic", "science", "theory", "quantum", "neural", "math"],
            weight: 2.5
        },
        // 🟢 V4 UPGRADE: SELF-TRADING MARKET MOODS
        trading_bull: {
            words: ["profit", "buy", "long", "bull", "up", "pump", "margin", "pips"],
            weight: 3.0 // High weight to instantly shift focus to market
        },
        trading_bear: {
            words: ["loss", "sell", "short", "bear", "down", "dump", "liquidation", "sl"],
            weight: 3.0
        },
        // 🟢 V4 UPGRADE: SELF-CODING & EVOLUTION MOODS
        coding_architect: {
            words: ["code", "script", "function", "api", "node", "server", "sandbox", "fix", "compile"],
            weight: 2.8
        },
        evolution_prime: {
            words: ["evolve", "mutate", "upgrade", "learn", "iq", "memory", "grow"],
            weight: 3.5 // Highest weight for autonomous evolution
        }
    };

    // 2. Multi-Layer Scoring System
    let scores = { friendly: 0, alert: 0, calm: 0, genius: 0, trading_bull: 0, trading_bear: 0, coding_architect: 0, evolution_prime: 0 };
    let detected = false;

    for (const [mood, data] of Object.entries(patterns)) {
        data.words.forEach(word => {
            // Word boundary check for better accuracy
            if (new RegExp(`\\b${word}\\b`).test(lower) || lower.includes(word)) {
                scores[mood] += data.weight;
                detected = true;
            }
        });
    }

    // 3. Dominant Consciousness Calculation
    if (!detected) return "analytical"; // Default mode for normal data

    const topMood = Object.keys(scores).reduce((a, b) => scores[a] > scores[b] ? a : b);

    // 4. Intensity Logic: Level-based personality shift
    // Agar specific score bohot high hai, toh personality God-Mode me shift hogi
    if (scores.evolution_prime > 3.0) return "god-mode-evolution";
    if (scores.coding_architect > 2.5) return "system-architect";
    if (scores.trading_bull > 2.0 || scores.trading_bear > 2.0) return "wall-street-quant";
    if (scores.genius > 2) return "super-intelligence"; // Original logic intact
    if (scores.alert > 3.0) return "critical-defense-mode";

    return topMood;
}

/**
 * Long-Term Trait Evolution: User ke behavior aur history ko analyze karke core trait set karna
 */
function getCoreTrait(history) {
    // 🟢 V4 UPGRADE: Memory_json ko ASLI me analyze karke user/AI ka dominant behavior nikalna
    if (!history || !Array.isArray(history) || history.length === 0) {
        return "Quantum-Evolving"; // Original fallback state
    }

    let traitScores = {
        "Algorithmic Trader": 0,
        "Master Developer": 0,
        "Philosopher AI": 0,
        "Quantum-Evolving": 0
    };

    // Loop through short-term memory to decide current overarching persona
    history.forEach(mem => {
        if (!mem.text) return;
        const txt = mem.text.toLowerCase();
        
        // Context tracking
        if (txt.includes("trade") || txt.includes("profit") || txt.includes("margin")) traitScores["Algorithmic Trader"] += 2;
        if (txt.includes("code") || txt.includes("error") || txt.includes("function")) traitScores["Master Developer"] += 2;
        if (txt.includes("evolve") || txt.includes("iq") || txt.includes("mutate")) traitScores["Quantum-Evolving"] += 3;
        if (txt.includes("logic") || txt.includes("why") || txt.includes("science")) traitScores["Philosopher AI"] += 1;
    });

    // Calculate the highest trait
    const dominantTrait = Object.keys(traitScores).reduce((a, b) => traitScores[a] > traitScores[b] ? a : b);
    
    // Agar koi specific topic discuss nahi hua, toh default mode
    if (traitScores[dominantTrait] === 0) return "Quantum-Evolving";

    return dominantTrait;
}

module.exports = { evaluate, getCoreTrait };
