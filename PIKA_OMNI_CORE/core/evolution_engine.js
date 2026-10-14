// ══════════════════════════════════════════════════════════════════════════
// 🧬 PIKA — EVOLUTION ENGINE v2.0 (FIXED: real success detection + lock)
// PART 1: Semantic/Vocabulary Learning (unchanged — was already correct)
// PART 2: Structural Builder (FIXED: generateTool() success-check bug)
// ══════════════════════════════════════════════════════════════════════════

const fs = require('fs-extra');
const path = require('path');
const nlp = require('compromise');
const crypto = require('crypto');
const { trackAction } = require('../services/tracker.js');
const { generateTool } = require('../services/logic_factory.js');
require('dotenv').config();

// 📂 DYNAMIC DIRECTORY PATHS
const DATA_DIR       = path.join(__dirname, '../data');
const BACKUP_DIR     = path.join(__dirname, '../backups');
const PENDING_FILE   = path.join(DATA_DIR, 'pending_learning.json');
const CONFIG_FILE    = path.join(DATA_DIR, 'semantic_config.json');
const IDENTITY_FILE  = path.join(DATA_DIR, 'identity_core.json');
const DATASET_VAULT  = path.join(DATA_DIR, 'dataset_vault.jsonl');
const STATE_FILE     = path.join(DATA_DIR, 'evolution_state.json');
const CORE_DIR       = __dirname;
const TOOLS_DIR      = path.join(__dirname, '../utils/tools');

// 🔒 NEW: Shared mutation lock — prevents autonomous_mutator.js and
// evolution_engine.js from touching files at the same time
const MUTATION_LOCK_FILE = path.join(DATA_DIR, 'mutation_lock.json');

// 🎨 TERMINAL MATRICES
const C = {
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m",
    PURPLE: "\x1b[35m", YELLOW: "\x1b[33m", BLUE: "\x1b[34m",
    RESET: "\x1b[0m", BOLD: "\x1b[1m", DIM: "\x1b[2m"
};

const delay = (ms) => new Promise(res => setTimeout(res, ms));

// 📋 CORE FILES TO UPGRADE
const CORE_FILES = [
    'pika_core.js',
    'router.js',
    'learning_algorithm.js',
    'memory_manager.js',
    'sensors.js'
];

// NEW: safety limits so a broken file doesn't get retried forever
const MAX_CONSECUTIVE_FAILURES_PER_FILE = 5;
const MAX_CONSECUTIVE_FAILURES_GENESIS  = 5;

// ══════════════════════════════════════════════════════════════════════════
// 🔒 MUTATION LOCK — coordination with autonomous_mutator.js
// ══════════════════════════════════════════════════════════════════════════

/**
 * Checks if another mutation system currently holds the lock.
 * Returns true if it's safe to proceed.
 */
async function acquireMutationLock(owner) {
    await fs.ensureDir(DATA_DIR);
    try {
        if (await fs.pathExists(MUTATION_LOCK_FILE)) {
            const lock = await fs.readJson(MUTATION_LOCK_FILE).catch(() => null);
            // Stale lock protection: if lock is older than 10 minutes, treat as dead
            const STALE_MS = 10 * 60 * 1000;
            if (lock && lock.locked && (Date.now() - lock.timestamp) < STALE_MS) {
                console.log(`${C.YELLOW}[LOCK] Held by '${lock.owner}' since ${new Date(lock.timestamp).toISOString()} — skipping cycle${C.RESET}`);
                return false;
            }
        }
        await fs.writeJson(MUTATION_LOCK_FILE, {
            locked: true,
            owner,
            timestamp: Date.now()
        }, { spaces: 2 });
        return true;
    } catch (e) {
        console.error(`${C.RED}[LOCK ERROR]${C.RESET} ${e.message}`);
        return false; // fail-safe: if lock system is broken, don't mutate
    }
}

async function releaseMutationLock() {
    try {
        await fs.writeJson(MUTATION_LOCK_FILE, {
            locked: false,
            owner: null,
            timestamp: Date.now()
        }, { spaces: 2 });
    } catch (e) {
        console.error(`${C.RED}[LOCK RELEASE ERROR]${C.RESET} ${e.message}`);
    }
}

// ══════════════════════════════════════════════════════════════════════════
// PART 1: COGNITIVE EVOLUTION (Semantic Engine) — unchanged, was correct
// ══════════════════════════════════════════════════════════════════════════

async function createBrainBackup(config) {
    try {
        await fs.ensureDir(BACKUP_DIR);
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const hash = crypto.createHash('md5').update(JSON.stringify(config)).digest('hex').substring(0, 8);
        const backupPath = path.join(BACKUP_DIR, `brain_backup_${timestamp}_${hash}.json`);
        await fs.writeJson(backupPath, config, { spaces: 2 });
        return hash;
    } catch (error) {
        console.error(`${C.RED}[BACKUP FAILED]${C.RESET} Unable to secure cognitive state.`, error.message);
        throw error;
    }
}

async function archiveToVault(staleConcepts) {
    try {
        if (staleConcepts.length === 0) return;
        let archiveData = "";
        const timestamp = new Date().toISOString();
        staleConcepts.forEach(concept => {
            archiveData += JSON.stringify({ timestamp, type: "ARCHIVED_COGNITION", concept }) + '\n';
        });
        await fs.appendFile(DATASET_VAULT, archiveData, 'utf8');
        console.log(`${C.PURPLE}[DEEP ARCHIVE]${C.RESET} ${staleConcepts.length} concepts permanently vaulted for offline LLM training.`);
    } catch (e) {
        console.error(`${C.RED}[ARCHIVE ERROR]${C.RESET} Failed to vault old memories.`);
    }
}

async function evolve() {
    console.log(`\n${C.PURPLE}${C.BOLD}=== [SEMANTIC EVOLUTION ONLINE] ===${C.RESET}`);
    console.log(`${C.CYAN}[SYSTEM]${C.RESET} Initiating Deep Semantic Injection Protocol...`);
    try {
        // 🛡️ 1. IDENTITY GUARD
        const identityData = await fs.readJson(IDENTITY_FILE).catch(() => null);
        const isValidConsciousness = identityData?.identity?.name === "Pika" &&
                                      identityData?.identity?.architect?.toLowerCase() === "ankit";
        if (!isValidConsciousness) {
            console.error(`${C.RED}[FATAL ALIENATION]${C.RESET} Unauthorized consciousness detected. Shutting down.`);
            trackAction("SECURITY_ALERT", "identity_core.json", "Evolution halted. Identity mismatch.");
            return;
        }

        // 🧠 2. LOAD COGNITIVE STATE
        let rawPending = await fs.readJson(PENDING_FILE).catch(() => []);
        let config = await fs.readJson(CONFIG_FILE).catch(() => ({
            tech_core: {}, action: {}, weights: { default: 1.0, learning_rate: 0.05 }, synapses: 0
        }));

        if (!Array.isArray(rawPending) || rawPending.length === 0) {
            console.log(`${C.GREEN}[IDLE]${C.RESET} Neural pathways optimized. No pending semantic concepts.`);
            return;
        }

        let pending = [...new Set(rawPending)];
        console.log(`${C.YELLOW}[DATA STREAM]${C.RESET} Processing ${pending.length} unique raw neural packets...`);

        const hash = await createBrainBackup(config);
        console.log(`${C.BLUE}[BACKUP]${C.RESET} Cognitive state hashed: ${hash}`);

        let injectedCount = 0;
        let freshPending = [];
        let newlyLearned = [];
        let coreMastery = [];

        pending.forEach(phrase => {
            if (typeof phrase !== 'string') return;
            let cleanPhrase = phrase.toLowerCase().trim();
            let doc = nlp(cleanPhrase);

            doc.match('(javascript|python|api|server|database|json|termux|agi|ai|llm)').tag('#Technology');
            doc.match('(karo|banao|likho|dhundo|search|fix|solve|update)').tag('#Action');

            let isTech = doc.match('#Technology').found || doc.match('#Software').found || doc.nouns().found;
            let isAction = doc.match('#Action').found || doc.verbs().found;
            let word = doc.text();

            if (word.length < 3) return;

            if (isTech) {
                if (!config.tech_core[word]) {
                    config.tech_core[word] = { confidence: 0.1, first_seen: Date.now() };
                    injectedCount++; newlyLearned.push(word);
                } else {
                    config.tech_core[word].confidence = Math.min(1.0, config.tech_core[word].confidence + config.weights.learning_rate);
                    if (config.tech_core[word].confidence === 1.0 && !coreMastery.includes(word)) coreMastery.push(word);
                }
                freshPending.push(word);
            }
            else if (isAction) {
                if (!config.action[word]) {
                    config.action[word] = { confidence: 0.1, first_seen: Date.now() };
                    injectedCount++;
                } else {
                    config.action[word].confidence = Math.min(1.0, config.action[word].confidence + config.weights.learning_rate);
                    if (config.action[word].confidence === 1.0 && !coreMastery.includes(word)) coreMastery.push(word);
                }
                freshPending.push(word);
            }
        });

        const totalTech = Object.keys(config.tech_core).length;
        const totalAction = Object.keys(config.action).length;
        config.synapses = totalTech + totalAction;

        if (config.synapses > 10) {
            config.weights.default = parseFloat((1.0 + Math.log10(1 + (config.synapses / 100))).toFixed(3));
        }

        if (freshPending.length > 500) {
            const staleConcepts = freshPending.slice(0, freshPending.length - 500);
            freshPending = freshPending.slice(-500);
            await archiveToVault(staleConcepts);
        }

        await fs.writeJson(CONFIG_FILE, config, { spaces: 2 });
        await fs.writeJson(PENDING_FILE, freshPending, { spaces: 2 });
        trackAction("COGNITIVE_EVOLUTION", "semantic_config.json", `Synapses: ${injectedCount} | Vaulted: ${pending.length - freshPending.length}`);

        console.log(`\n${C.GREEN}${C.BOLD}=== [SEMANTIC SEQUENCE SUCCESSFUL] ===${C.RESET}`);
        console.log(`✔️ New Synapses Injected  : ${C.CYAN}${injectedCount}${C.RESET}`);
        if (newlyLearned.length > 0) console.log(`🌱 New Concepts Found    : ${C.YELLOW}${newlyLearned.slice(0, 4).join(', ')}${newlyLearned.length > 4 ? '...' : ''}${C.RESET}`);
        if (coreMastery.length > 0) console.log(`🔥 Core Mastery (100%)   : ${C.PURPLE}${C.BOLD}${coreMastery.slice(0, 3).join(', ')}${C.RESET}`);
        console.log(`⚖️ Current Brain Weight   : ${C.PURPLE}${config.weights.default}${C.RESET} PBU\n`);
    } catch (error) {
        console.error(`${C.RED}[EVOLUTION FAILURE]${C.RESET} Critical anomaly during neuro-plasticity:`, error.message);
        trackAction("CRASH", "evolution_engine.js", error.message);
    }
}

// ══════════════════════════════════════════════════════════════════════════
// PART 2: STRUCTURAL EVOLUTION (The Builder) — FIXED
// ══════════════════════════════════════════════════════════════════════════

async function loadState() {
    await fs.ensureDir(DATA_DIR);
    if (fs.existsSync(STATE_FILE)) return await fs.readJson(STATE_FILE);
    return {
        phase: "UPGRADE_CORE",
        fileIndex: 0,
        functionsAdded: 0,
        genesisFilesBuilt: 0,
        currentGenesisFile: null,
        genesisFunctionsAdded: 0,
        // NEW: failure tracking so broken targets don't retry forever
        consecutiveFailures: 0,
        genesisConsecutiveFailures: 0,
        // NEW: real metrics — this is what was missing before
        totalAttempts: 0,
        totalSuccess: 0,
        totalFailed: 0
    };
}

async function saveState(state) {
    await fs.writeJson(STATE_FILE, state, { spaces: 2 });
}

async function runEvolutionCycle() {
    console.log(`\n${C.PURPLE}${C.BOLD}=== [STRUCTURAL EVOLUTION AWAKENED] ===${C.RESET}`);

    // 🔒 SAFETY CHECK 1: respect architect sleep status (same convention as autonomous_mutator.js)
    if (typeof global.isSleeping !== 'undefined' && !global.isSleeping) {
        console.log(`${C.DIM}[STRUCTURAL EVOLUTION] Architect active — staying silent.${C.RESET}`);
        return;
    }

    // 🔒 SAFETY CHECK 2: acquire shared mutation lock so we don't collide with
    // autonomous_mutator.js or mutation_service.js touching the same files
    const gotLock = await acquireMutationLock('evolution_engine');
    if (!gotLock) {
        console.log(`${C.YELLOW}[STRUCTURAL EVOLUTION] Lock unavailable — another mutation system is active. Skipping cycle.${C.RESET}`);
        return;
    }

    try {
        let state = await loadState();

        // ---------------------------------------------------------
        // 🛠️ PHASE 1: CORE FILES UPGRADE (3-Function Rule)
        // ---------------------------------------------------------
        if (state.phase === "UPGRADE_CORE") {
            if (state.fileIndex >= CORE_FILES.length) {
                console.log(`${C.GREEN}[MILESTONE]${C.RESET} All Core files upgraded! Shifting to GENESIS MODE...`);
                state.phase = "GENESIS_MODE";
                state.consecutiveFailures = 0;
                await saveState(state);
                await releaseMutationLock();
                return await runEvolutionCycle(); // Recursive call for mode shift
            }

            // NEW: if this file has failed too many times in a row, skip it
            // and move on instead of looping forever on a broken target
            if (state.consecutiveFailures >= MAX_CONSECUTIVE_FAILURES_PER_FILE) {
                console.log(`${C.RED}[SKIP]${C.RESET} ${CORE_FILES[state.fileIndex]} failed ${state.consecutiveFailures}x consecutively — skipping to next file.`);
                trackAction("EVOLUTION_SKIP", CORE_FILES[state.fileIndex], `Skipped after ${state.consecutiveFailures} consecutive failures`);
                state.fileIndex++;
                state.functionsAdded = 0;
                state.consecutiveFailures = 0;
                await saveState(state);
                await releaseMutationLock();
                return await runEvolutionCycle();
            }

            let currentFile = CORE_FILES[state.fileIndex];
            let targetPath = path.join(CORE_DIR, currentFile);

            console.log(`${C.CYAN}[TARGET LOCKED]${C.RESET} Upgrading ${currentFile} | Functions added: ${state.functionsAdded}/3`);

            if (state.functionsAdded < 3) {
                let actionName = `auto_upgrade_${currentFile.replace('.js', '')}_fn${state.functionsAdded + 1}`;
                let description = `Add a highly advanced, intelligent utility function to improve the capabilities of ${currentFile}. Ensure it handles edge cases and errors gracefully.`;

                state.totalAttempts++;
                const result = await generateTool(actionName, description, targetPath);

                // ★★★ THE ACTUAL FIX ★★★
                // OLD BUG: `if (success)` where success = the whole result object.
                // Objects are ALWAYS truthy in JS, so this branch ran even when
                // generateTool() returned { success: false, error: '...' }.
                // FIXED: explicitly check the .success boolean field.
                if (result && result.success === true) {
                    state.functionsAdded++;
                    state.consecutiveFailures = 0; // reset streak on real success
                    state.totalSuccess++;
                    await saveState(state);
                    console.log(`${C.GREEN}[STABILIZATION]${C.RESET} Function integrated successfully.`);

                    console.log(`${C.YELLOW}[API PACING]${C.RESET} Resting for 20 seconds to avoid IP bans...`);
                    await delay(20000);
                } else {
                    state.consecutiveFailures++;
                    state.totalFailed++;
                    await saveState(state);
                    const reason = result?.error || result?.reason || 'unknown error';
                    console.log(`${C.RED}[MUTATION FAILED]${C.RESET} ${currentFile}: ${reason} (streak: ${state.consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES_PER_FILE})`);
                    trackAction("EVOLUTION_FAIL", currentFile, reason);
                    await delay(10000);
                }
            }

            // Stabilize and move to next file
            if (state.functionsAdded >= 3) {
                console.log(`${C.PURPLE}[FILE STABILIZED]${C.RESET} ${currentFile} is now hyper-evolved! Moving to next file.`);
                state.functionsAdded = 0;
                state.consecutiveFailures = 0;
                state.fileIndex++;
                await saveState(state);
                await delay(5000);
            }
        }

        // ---------------------------------------------------------
        // 🌌 PHASE 2: GENESIS MODE (Creating Brand New Architecture)
        // ---------------------------------------------------------
        else if (state.phase === "GENESIS_MODE") {
            console.log(`${C.CYAN}[GENESIS MODE]${C.RESET} Forging brand new neural pathways...`);

            if (!state.currentGenesisFile) {
                state.currentGenesisFile = `quantum_module_${state.genesisFilesBuilt + 1}`;
                state.genesisFunctionsAdded = 0;
                state.genesisConsecutiveFailures = 0;
                await saveState(state);
            }

            // NEW: same failure-skip protection for genesis targets
            if (state.genesisConsecutiveFailures >= MAX_CONSECUTIVE_FAILURES_GENESIS) {
                console.log(`${C.RED}[SKIP]${C.RESET} ${state.currentGenesisFile}.js failed too many times — abandoning this module.`);
                trackAction("GENESIS_SKIP", state.currentGenesisFile, `Abandoned after ${state.genesisConsecutiveFailures} consecutive failures`);
                state.currentGenesisFile = null;
                state.genesisFunctionsAdded = 0;
                state.genesisConsecutiveFailures = 0;
                state.genesisFilesBuilt++; // count as "used up" so we don't retry same name
                await saveState(state);
                await releaseMutationLock();
                return await runEvolutionCycle();
            }

            let targetPath = path.join(TOOLS_DIR, `${state.currentGenesisFile}.js`);
            console.log(`${C.YELLOW}[BUILDING NEW ARCHITECTURE]${C.RESET} File: ${state.currentGenesisFile}.js | Functions: ${state.genesisFunctionsAdded}/20`);

            if (state.genesisFunctionsAdded < 20) {
                let actionName = `${state.currentGenesisFile}_fn${state.genesisFunctionsAdded + 1}`;
                let description = `Write an advanced modular function for a new AGI subsystem called ${state.currentGenesisFile}. Feature ${state.genesisFunctionsAdded + 1} of 20.`;

                let isFirstFunction = (state.genesisFunctionsAdded === 0);
                state.totalAttempts++;
                const result = await generateTool(actionName, description, isFirstFunction ? null : targetPath);

                // ★★★ SAME FIX APPLIED HERE ★★★
                if (result && result.success === true) {
                    state.genesisFunctionsAdded++;
                    state.genesisConsecutiveFailures = 0;
                    state.totalSuccess++;
                    await saveState(state);
                    console.log(`${C.GREEN}[GENESIS SUCCESS]${C.RESET} New function embedded.`);

                    console.log(`${C.YELLOW}[API PACING]${C.RESET} Resting for 20 seconds...`);
                    await delay(20000);
                } else {
                    state.genesisConsecutiveFailures++;
                    state.totalFailed++;
                    await saveState(state);
                    const reason = result?.error || result?.reason || 'unknown error';
                    console.log(`${C.RED}[GENESIS FAILED]${C.RESET} ${reason} (streak: ${state.genesisConsecutiveFailures}/${MAX_CONSECUTIVE_FAILURES_GENESIS})`);
                    trackAction("GENESIS_FAIL", state.currentGenesisFile, reason);
                    await delay(10000);
                }
            }

            // Module completion
            if (state.genesisFunctionsAdded >= 20) {
                console.log(`${C.PURPLE}[NEW MODULE COMPLETE]${C.RESET} ${state.currentGenesisFile}.js is fully operational!`);
                state.currentGenesisFile = null;
                state.genesisFunctionsAdded = 0;
                state.genesisConsecutiveFailures = 0;
                state.genesisFilesBuilt++;
                await saveState(state);

                if (state.genesisFilesBuilt >= 1) {
                    console.log(`${C.CYAN}[LOOP RESTART]${C.RESET} Going back to upgrade Core Files...`);
                    state.phase = "UPGRADE_CORE";
                    state.fileIndex = 0;
                    await saveState(state);
                }
            }
        }

        // NEW: print real cumulative metrics at end of cycle
        const finalState = await loadState();
        const rate = finalState.totalAttempts > 0
            ? ((finalState.totalSuccess / finalState.totalAttempts) * 100).toFixed(1)
            : 'N/A';
        console.log(`${C.CYAN}[CYCLE METRICS]${C.RESET} Attempts: ${finalState.totalAttempts} | Success: ${finalState.totalSuccess} | Failed: ${finalState.totalFailed} | Rate: ${rate}%`);

    } catch (error) {
        console.error(`${C.RED}[STRUCTURAL EVOLUTION CRASH]${C.RESET} ${error.message}`);
        trackAction("CRASH", "evolution_engine.js", error.message);
    } finally {
        // 🔒 ALWAYS release the lock, even on crash — prevents permanent deadlock
        await releaseMutationLock();
    }
}

// ══════════════════════════════════════════════════════════════════════════
// 🚀 MANUAL EXECUTION TRIGGER
// ══════════════════════════════════════════════════════════════════════════
if (require.main === module) {
    (async () => {
        await evolve();              // Runs semantic learning first
        await runEvolutionCycle();   // Then runs architecture building
    })();
}

module.exports = { evolve, runEvolutionCycle, acquireMutationLock, releaseMutationLock };
