// =====================================================================
// 🧹 PKA CLEANER.JS : NEURAL SANITIZER [GOD-MODE UPGRADE]
// Smart Vocabulary Purification | 100% API-FREE | Noise Reduction
// =====================================================================

const fs = require('fs');
const path = require('path');

// Assuming cleaner.js is in the root directory
const statePath = path.join(__dirname, "runtime", "state.json");

async function runSmartCleanup() {
    console.log("\x1b[36m%s\x1b[0m", "==========================================================");
    console.log("\x1b[35m%s\x1b[0m", " ✨ INITIATING SMART NEURAL SANITIZATION (API-FREE)... ");
    console.log("\x1b[36m%s\x1b[0m", "==========================================================");

    try {
        if (!fs.existsSync(statePath)) return console.log("⚠️ state.json missing!");

        let state = JSON.parse(fs.readFileSync(statePath, 'utf8'));

        if (!state.vocabulary) state.vocabulary = [];
        if (!state.grammar) state.grammar = {};

        const originalCount = state.vocabulary.length;

        // 🏗️ PHASE 1: HARD FILTER (HTML/CSS & Syntax Junk)
        console.log("🧹 [PHASE 1] Running Hard-Pattern filtering...");
        const junkPatterns = [
            "navbar", "display", "block", "footer", "header", "css", "href", "div", "span",
            "http", "https", "www", "com", "org", "function", "return", "var", "let", "const",
            "margin", "padding", "rgba", "script", "style", "html", "body", "json", "true",
            "false", "null", "undefined", "src", "alt", "class", "id", "align", "border"
        ];

        // 🧠 PHASE 2: ALGORITHMIC NOISE REDUCTION (Replaces Gemini API)
        console.log("🧠 [PHASE 2] Algorithmic Entropy & Noise Reduction...");

        state.vocabulary = state.vocabulary.filter(word => {
            let w = word.toLowerCase().trim();

            // 1. Junk Pattern Match
            const isJunk = junkPatterns.some(j => w === j || w.includes(j));

            // 2. Contains numbers, special chars, or looks like a hex/hash
            const hasNumbersOrSymbols = /[^a-z]/i.test(w);

            // 3. Length Constraints (Too short or unnaturally long concatenations)
            const invalidLength = w.length < 3 || w.length > 15;

            // 4. Gibberish Detection (5+ consecutive consonants = definitely junk)
            const isGibberish = /[bcdfghjklmnpqrstvwxyz]{5,}/i.test(w);

            // Keep the word only if it passes ALL filters
            return !isJunk && !hasNumbersOrSymbols && !invalidLength && !isGibberish;
        });

        // 🕸️ PHASE 3: DEAD SYNAPSE PRUNING (Grammar Cleanup)
        console.log("🕸️ [PHASE 3] Pruning Dead Synapses (N-Gram Cleanup)...");
        let prunedSynapses = 0;

        for (let context in state.grammar) {
            for (let target in state.grammar[context]) {
                // Check if the target word or context words were deleted from vocabulary
                const contextWords = context.split(" ");
                if (!state.vocabulary.includes(target) ||
                    !state.vocabulary.includes(contextWords[0]) ||
                    (contextWords[1] && !state.vocabulary.includes(contextWords[1]))) {

                    delete state.grammar[context][target];
                    prunedSynapses++;
                }
            }
            // Delete context node entirely if it's empty now
            if (Object.keys(state.grammar[context]).length === 0) {
                delete state.grammar[context];
            }
        }

        // 📈 PHASE 4: RE-CALIBRATION (God-Mode Logic)
        // Intelligence is now a factor of pure vocabulary AND active synapses
        state.intelligence = (state.vocabulary.length * 1.5) + (Object.keys(state.grammar).length * 0.5);

        fs.writeFileSync(statePath, JSON.stringify(state, null, 2));

        // 🖥️ HACKER UI
        const removed = originalCount - state.vocabulary.length;
        console.log("\n\x1b[32m%s\x1b[0m", " ✅ CLEAN-UP COMPLETE!");
        console.log(` 🗑️ Words Removed     : ${removed}`);
        console.log(` 🕸️ Synapses Pruned   : ${prunedSynapses}`);
        console.log(` 💎 Pure Vocabulary   : ${state.vocabulary.length}`);
        console.log(` 🧠 Adjusted Intel    : ${state.intelligence.toFixed(2)}`);
        console.log("\x1b[35m%s\x1b[0m", "==========================================================");

    } catch (e) {
        console.error("❌ Cleanup Error: " + e.message);
    }
}

runSmartCleanup();
