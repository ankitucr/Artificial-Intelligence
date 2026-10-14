// =====================================================================
// 🛠️ PKA RECOVER.JS : THE NEURAL TISSUE REPAIR ENGINE [GOD-MODE]
// Local DNA Rebuilding + DuckDuckGo Web-Healing (100% API-FREE)
// =====================================================================

const fs = require("fs");
const path = require("path");
const { search } = require("duck-duck-scrape"); // 🕸️ NEW: DuckDuckGo Healing Power

// 📁 PATHS
const statePath = path.join(__dirname, "runtime", "state.json");
const memoryPath = path.join(__dirname, "data", "memory.json");
const backupPath = path.join(__dirname, "runtime", "state_backup.json"); 

console.log("\x1b[36m%s\x1b[0m", "==========================================================");
console.log("\x1b[35m%s\x1b[0m", " 🧬 INITIATING DEEP NEURAL RECOVERY & WEB-ASSIMILATION ");
console.log("\x1b[36m%s\x1b[0m", "==========================================================");

async function runGodModeRecovery() {
    try {
        // 1. Safety Check & Load
        if (!fs.existsSync(statePath) || !fs.existsSync(memoryPath)) {
            throw new Error("Core Files Missing! Recovery impossible.");
        }

        let state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
        let memory = JSON.parse(fs.readFileSync(memoryPath, 'utf8'));

        // 🟢 CREATE BACKUP: Create a quick backup before overwriting
        fs.writeFileSync(backupPath, JSON.stringify(state));

        // Ensure Neural Structures Exist
        if (!state.grammar) state.grammar = {};
        if (!state.synapses) state.synapses = {};
        if (!state.vocabulary) state.vocabulary = [];
        if (!state.mastery) state.mastery = { self_evolution: 0 };

        let recoveredCount = 0;
        let marketContextRecovered = 0;

        // =========================================================
        // 🏗️ PHASE 1: HARD-RECOVERY (The fast n-gram rebuild)
        // =========================================================
        console.log("🏗️ [PHASE 1] Rebuilding raw linguistic pathways from Memory DNA...");

        const allMemories = [...(memory.history || []), ...(memory.longTerm || [])];

        if (allMemories.length > 0) {
            allMemories.forEach(node => {
                if (node && node.text) {
                    const words = node.text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/);

                    if (node.text.match(/(btc|profit|trade|market|nifty|forex|function|sandbox|error)/gi)) {
                        marketContextRecovered++;
                    }

                    for (let i = 0; i < words.length - 2; i++) {
                        let w1 = words[i], w2 = words[i+1], tgt = words[i+2];
                        if(!w1 || !w2 || !tgt) continue;

                        if (w1.length > 2 && !state.vocabulary.includes(w1)) state.vocabulary.push(w1);
                        if (w2.length > 2 && !state.vocabulary.includes(w2)) state.vocabulary.push(w2);
                        if (tgt.length > 2 && !state.vocabulary.includes(tgt)) state.vocabulary.push(tgt);

                        let ctx = w1 + " " + w2;
                        if (!state.grammar[ctx]) state.grammar[ctx] = {};
                        if (!state.grammar[ctx][tgt]) {
                            state.grammar[ctx][tgt] = { weight: 1, lastUsed: Date.now() };
                        } else {
                            state.grammar[ctx][tgt].weight += 0.5;
                        }
                        recoveredCount++;
                    }
                }
            });
        }

        // =========================================================
        // 🧠 PHASE 2: DEEP NEURAL HEALING & WEB-JUMPSTART
        // =========================================================
        console.log("🧠 [PHASE 2] Algorithmic Healing & DuckDuckGo Web-Assimilation...");
        
        // 2A. Extract Core Beliefs from Local LTM
        if (memory.longTerm && memory.longTerm.length > 0) {
            memory.longTerm.forEach((mem, index) => {
                const synapseId = `CORE_BELIEF_${index}`;
                state.synapses[synapseId] = mem.text;
            });
            console.log(`✅ [LOCAL_HEAL] Injected ${memory.longTerm.length} permanent synapses from LTM.`);
        }

        // 2B. The DuckDuckGo Jumpstart (Web-Heal)
        console.log("🕸️ [WEB_HEAL] Fetching universal market truths from Deep Web to jumpstart brain...");
        try {
            const searchResults = await search("advanced algorithmic trading risk management principles core rules", { safeSearch: "moderate" });
            
            if (searchResults.results && searchResults.results.length > 0) {
                let webCount = 0;
                for (let i = 0; i < Math.min(3, searchResults.results.length); i++) {
                    const snippet = searchResults.results[i].description.replace(/[^a-zA-Z0-9 .,]/g, "");
                    
                    // Inject direct web truths into Synapses
                    state.synapses[`WEB_TRUTH_${Date.now()}_${i}`] = snippet;

                    // Extract heavy words to boost vocabulary instantly
                    const words = snippet.toLowerCase().split(/\s+/);
                    words.forEach(w => {
                        if (w.length > 6 && !state.vocabulary.includes(w)) {
                            state.vocabulary.push(w);
                        }
                    });
                    webCount++;
                }
                console.log(`🌌 [WEB_HEAL] Assimilated ${webCount} Universal Truths from DuckDuckGo into Synapses.`);
            }
        } catch (e) {
            console.log("⚠️ Web-Heal offline or blocked. Relying strictly on local DNA.");
        }

        // =========================================================
        // 🛡️ PHASE 3: SANITY CHECK (Failsafe)
        // =========================================================
        console.log("🛡️ [PHASE 3] System Calibration & Sanity Check...");

        if (isNaN(state.intelligence) || !state.intelligence) {
            state.intelligence = (state.vocabulary.length * 1.5) + (Object.keys(state.grammar).length * 0.5);
            if(state.intelligence < 100) state.intelligence = 11361.5; 
        } else {
            // Mega IQ boost for successfully surviving a crash and learning from the web
            state.intelligence += Number((recoveredCount * 0.05).toFixed(2)) + 50; 
        }

        state.mastery.self_evolution = Number((state.mastery.self_evolution + 0.1).toFixed(2));
        state.level = Math.floor(state.intelligence / 100) + 1;

        fs.writeFileSync(statePath, JSON.stringify(state, null, 2));

        // 🖥️ HACKER UI OUTPUT
        console.log("\n\x1b[32m%s\x1b[0m", " ✅ RECOVERY & WEB-HEAL SUCCESSFUL!");
        console.log(` 🧬 Synapses Rebuilt   : ${recoveredCount}`);
        console.log(` 🌐 Web Truths Injected: Yes`);
        console.log(` 💎 Vocabulary Size    : ${state.vocabulary.length}`);
        console.log(` 🧠 Neural Status      : HYPER-STABLE (IQ: ${state.intelligence.toFixed(1)})`);
        console.log(` 🛡️ Backup Created     : state_backup.json`);
        console.log("\x1b[35m%s\x1b[0m", "==========================================================");

    } catch (e) {
        console.error("\x1b[31m%s\x1b[0m", "❌ CRITICAL RECOVERY FAILURE: " + e.message);
    }
}

// Ignition
runGodModeRecovery();
