const fs = require('fs-extra');                                   
const path = require('path');
const { trackAction } = require('../services/tracker.js'); // 🛡️ Synced with Nervous System

// 📂 DYNAMIC ARCHITECTURE PATHS
const DATA_DIR = path.join(__dirname, '../data');
const CONFIG_PATH = path.join(__dirname, '../data/semantic_config.json');
const DATASET_VAULT = path.join(DATA_DIR, 'dataset_vault.jsonl'); // 🌌 THE INFINITE ARCHIVE

// 🎨 TERMINAL MATRICES
const C = { 
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m", 
    YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", RESET: "\x1b[0m", BOLD: "\x1b[1m" 
};

// 📚 CORE MEMORY SECTORS
const MEMORY_FILES = {
    CORE: 'deep_knowledge.json',                                  
    APP: 'app_logic.json',
    TECH: 'technical_docs.json',
    PERSONAL: 'personal_notes.json',
    SKILLS: 'skills_vault.json',                                  
    VAULT: 'code_vault.json'
};

fs.ensureDirSync(DATA_DIR);                                       

// ==========================================
// ♾️ THE ELASTIC RAM CACHE (Auto-Scaling)
// ==========================================
let RAM_CACHE = {};
const MAX_CACHE_SIZE = 5000; // Safe threshold for Termux V8 Engine

async function readMemory(fileName) {
    try {
        if (RAM_CACHE[fileName]) return RAM_CACHE[fileName];      

        const filePath = path.join(DATA_DIR, fileName);
        if (!fs.existsSync(filePath)) return {};

        const data = await fs.readJson(filePath);
        RAM_CACHE[fileName] = data; // Lock into active RAM
        return data;
    } catch (e) {
        console.error(`${C.RED}[MEMORY READ ERROR]${C.RESET} Matrix mismatch in ${fileName}: ${e.message}`);
        return {};
    }                                                             
}

async function saveMemory(fileName, data) {
    try {                                                         
        const filePath = path.join(DATA_DIR, fileName);
        
        // Permanent Disk Commit
        await fs.writeJson(filePath, data, { spaces: 2 });
        RAM_CACHE[fileName] = data; // Sync RAM

        // 🛡️ DYNAMIC CACHE PURGE (Bulletproof size calculation)
        let dataSize = 0;
        if (Array.isArray(data)) {
            dataSize = data.length;
        } else if (typeof data === 'object' && data !== null) {
            dataSize = Object.keys(data).length;
        }
        
        if (dataSize > MAX_CACHE_SIZE) {
            console.log(`${C.YELLOW}[RAM OPTIMIZED]${C.RESET} ${fileName} exceeded safe threshold. Unloading from RAM (Disk state secured).`);
            delete RAM_CACHE[fileName];
        }

        // Telemetry
        if (typeof trackAction === 'function') {
            trackAction("DATA_CONSERVED", fileName, `Synaptic state committed to disk.`);
        }

    } catch (e) {
        console.error(`${C.RED}[MEMORY WRITE ERROR]${C.RESET} Failed to commit ${fileName}: ${e.message}`);
    }
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ==========================================
// 🌌 OMNI-SEARCH V12 (Pure Semantic & Temporal Retrieval)
// ==========================================
async function omniSearch(inputData) {
    try {                                                         
        // 1. Load Dynamic Weights (Unscripted AI Baseline)
        let config = { fillers: ['kya', 'hai', 'kaise', 'aur', 'the', 'is', 'what'], tech_core: {}, action: {} };                   
        if (fs.existsSync(CONFIG_PATH)) {
            let loadedConfig = await fs.readJson(CONFIG_PATH);
            config.tech_core = loadedConfig.tech_core || {};
            config.action = loadedConfig.action || {};
            config.fillers = loadedConfig.fillers || config.fillers;
        }                                                         

        let phraseArray = Array.isArray(inputData) ? inputData : [inputData];
        let fullPhrase = phraseArray.join(' ').toLowerCase().trim();

        if (typeof trackAction === 'function') {
            trackAction("OMNI_SEARCH", "Scanning Cosmic Lake", `Neural Targeting: ${fullPhrase}`);
        }

        if (!fullPhrase) return null;                             
        let scoredResults = [];
        let phraseRegex = new RegExp('\\b' + escapeRegExp(fullPhrase) + '\\b', 'i');

        // -----------------------------------------------------
        // 🧠 TIER 1: ACTIVE CORE SECTORS (Parallel Retrieval)
        // -----------------------------------------------------
        const categories = Object.keys(MEMORY_FILES);
        const memoryPromises = categories.map(category => readMemory(MEMORY_FILES[category]));
        const memories = await Promise.all(memoryPromises);

        for (let i = 0; i < categories.length; i++) {
            const category = categories[i];
            const memory = memories[i];

            // 🎯 EXACT NEURAL MATCH (Highest Pure Score)
            if (memory[fullPhrase]) {                             
                let content = memory[fullPhrase];
                let contentStr = typeof content === 'object' ? JSON.stringify(content, null, 2) : content;
                scoredResults.push({
                    score: 150,
                    text: `[${category} PRIMARY HIT] '${fullPhrase}':\n${contentStr}`                                               
                });
                continue;
            }

            // 🕸️ DYNAMIC SEMANTIC SCANNING
            for (let key in memory) {
                let keyLower = key.toLowerCase();
                if (keyLower === fullPhrase) continue;

                let content = memory[key];
                let matchScore = 0;

                // Sub-string match
                if (phraseRegex.test(keyLower)) {
                    matchScore += 75;
                }

                // Reverse Neural Association (Applying learned weights)
                if (!config.fillers.includes(keyLower) && (keyLower.length > 3 || config.tech_core[keyLower])) {
                    let keyRegex = new RegExp('\\b' + escapeRegExp(keyLower) + '\\b', 'i');                                         
                    if (keyRegex.test(fullPhrase)) {
                        let confidenceBonus = config.tech_core[keyLower] ? (config.tech_core[keyLower].confidence * 20) : 0;
                        matchScore += (55 + confidenceBonus); // Score adjusts dynamically based on Pika's learning
                    }
                }                                                 

                // Deep Vault Code Analysis Context
                if (category === 'VAULT' && typeof content === 'object') {
                    if (content.title && content.title.toLowerCase().includes(fullPhrase)) {
                        matchScore += 70;
                    } else if (content.source_code && content.source_code.toLowerCase().includes(fullPhrase)) {
                        matchScore += 50;
                    }
                }

                if (matchScore > 0) {                             
                    let contentStr = typeof content === 'object' ? JSON.stringify(content) : content;
                    scoredResults.push({
                        score: matchScore,
                        text: `[${category} Context] ${key}: ${contentStr}`
                    });
                }
            }
        }

        // -----------------------------------------------------
        // 🌌 TIER 2: THE DATASET VAULT (Unscripted Experience Mining)
        // -----------------------------------------------------
        if (fs.existsSync(DATASET_VAULT)) {
            const vaultData = await fs.readFile(DATASET_VAULT, 'utf8');
            const lines = vaultData.split('\n').filter(line => line.trim() !== '');
            
            lines.forEach(line => {
                try {
                    const record = JSON.parse(line);
                    // Dynamically aggregate all possible text fields without hardcoding specific schema assumptions
                    let searchSpace = Object.values(record)
                        .filter(val => typeof val === 'string')
                        .join(' ')
                        .toLowerCase();

                    if (phraseRegex.test(searchSpace)) {
                        // ⏳ TEMPORAL AWARENESS: Math-based bonus for recent records
                        let timeBonus = 0;
                        if (record.timestamp) {
                            let ageInDays = (Date.now() - new Date(record.timestamp).getTime()) / (1000 * 3600 * 24);
                            timeBonus = Math.max(0, 10 - ageInDays); // Fades dynamically over 10 days
                        }

                        scoredResults.push({
                            score: 60 + timeBonus, 
                            text: `[DEEP VAULT ARCHIVE]\n${JSON.stringify(record, null, 2)}`
                        });
                    }
                } catch (e) {
                    // Ignore corrupted JSONL lines gracefully
                }
            });
        }

        // -----------------------------------------------------
        // ⚖️ TOP-K RELEVANCE RANKING (Pure Math Sorting)
        // -----------------------------------------------------
        scoredResults.sort((a, b) => b.score - a.score);

        // Limit to Top 5 unique contexts to protect LLM token limits
        let topResults = scoredResults.slice(0, 5).map(item => item.text);
        let uniqueResults = [...new Set(topResults)];             
        
        if (uniqueResults.length > 0) {
            console.log(`${C.GREEN}[MEMORY SYNTHESIS]${C.RESET} Pika extracted ${uniqueResults.length} relevant cognitive blocks.`);
        }

        return uniqueResults.length > 0 ? uniqueResults.join('\n\n') : null;

    } catch (err) {
        console.error(`${C.RED}[OMNI-SEARCH FAILURE]${C.RESET} Memory pipeline disrupted:`, err.message);
        return null;                                              
    }
}

module.exports = { readMemory, saveMemory, omniSearch, MEMORY_FILES, RAM_CACHE };
