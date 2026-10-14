const fs = require('fs-extra');
const path = require('path');
const wikipedia = require('wikipedia');
const { OpenAI } = require('openai');
const Groq = require('groq-sdk');
const { exec } = require('child_process');
require('dotenv').config();

// ==========================================
// 🌐 HIVE MIND: SAFE IMPORTS
// ==========================================
const { analyzeInput } = require('./nlp_parser.js');
const { omniSearch } = require('./memory_manager.js');
const { runSensors } = require('./sensors.js');
const { trackAction } = require('../services/tracker.js');

// 🧠 NEW: Self-knowledge engine — Pika's OWN brain, checked BEFORE any API call
const { resolveWithSelfKnowledge } = require('./self_knowledge_engine.js');

// 🎨 PROFESSIONAL MATRIX COLORS
const C = {
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m",
    YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", RESET: "\x1b[0m", BOLD: "\x1b[1m"
};

const DATA_DIR = path.join(__dirname, '../data');
const CHAT_HISTORY_FILE = path.join(DATA_DIR, 'chat_history.json');
const DATASET_VAULT = path.join(DATA_DIR, 'dataset_vault.jsonl');
const BAYES_MODEL = path.join(DATA_DIR, 'pika_brain_bayes.json');
const PENDING_LEARNING_FILE = path.join(DATA_DIR, 'pending_learning.json'); // NEW

// Ensure data directories exist
(async () => {
    await fs.ensureDir(DATA_DIR);
    await fs.ensureDir(path.join(DATA_DIR, 'sandbox_tmp'));
})();

// ==========================================
// 🧹 THE 401 KILLER: KEY CLEANER
// ==========================================
const cleanKey = (key) => key ? key.replace(/\r/g, '').trim() : null;

// ==========================================
// 🌐 FETCH POLYFILL (Node 16/17 compatible)
// ==========================================
let fetch;
try {
    fetch = require('node-fetch');
} catch (e) {
    fetch = globalThis.fetch;
    if (!fetch) {
        console.log(`${C.RED}[FATAL]${C.RESET} node-fetch not installed. Run: npm i node-fetch@2`);
        process.exit(1);
    }
}

// ==========================================
// 🔄 THE ROUND-ROBIN API ENGINE (Groq + SambaNova)
// This part was ALREADY correct — 15 keys rotate via getNextClient().
// Groq/Samba remain the SUPPORT brain, not the main brain (see processMessage below).
// ==========================================
const groqClients = [];
const sambaClients = [];

for (let g = 1; g <= 13; g++) {
    const key = cleanKey(process.env[`GROQ_${g}`]);
    if (key) groqClients.push(new Groq({ apiKey: key }));
}

for (let s = 1; s <= 5; s++) {
    const key = cleanKey(process.env[`SAMBA_${s}`]);
    if (key) sambaClients.push(new OpenAI({ apiKey: key, baseURL: "https://api.sambanova.ai/v1" }));
}

console.log(`${C.GREEN}[SYSTEM BOOT]${C.RESET} Arsenal Loaded: ${groqClients.length}/13 Groq, ${sambaClients.length}/5 SambaNova keys.`);

let currentGroqTracker = 0;
let currentSambaTracker = 0;

function getNextClient(type = 'groq') {
    if (type === 'groq' && groqClients.length > 0) {
        const client = groqClients[currentGroqTracker];
        console.log(`${C.CYAN}[NETWORK SHIFT]${C.RESET} Routing through Groq Key #${currentGroqTracker + 1}`);
        currentGroqTracker = (currentGroqTracker + 1) % groqClients.length;
        return client;
    }
    if (type === 'samba' && sambaClients.length > 0) {
        const client = sambaClients[currentSambaTracker];
        console.log(`${C.CYAN}[NETWORK SHIFT]${C.RESET} Routing through SambaNova Key #${currentSambaTracker + 1}`);
        currentSambaTracker = (currentSambaTracker + 1) % sambaClients.length;
        return client;
    }
    return null;
}

const execPromise = (cmd) => new Promise((res, rej) =>
    exec(cmd, { maxBuffer: 1024 * 1024 * 5 }, (err, stdout, stderr) => {
        if (err) return rej(stderr || err.message);
        res(stdout || "");
    })
);

// ==========================================
// 🚦 ENTERPRISE API GATEWAY (Rate Limiter)
// ==========================================
const MAX_RPM = 15;
const TIME_WINDOW = 15 * 1000;
let requestTimestamps = [];
let taskQueue = [];
let isGateBusy = false;

async function executeNeuralTask(task, taskName = "System_Task") {
    return new Promise((resolve, reject) => {
        taskQueue.push({ task, resolve, reject, taskName });
        processGateQueue();
    });
}

async function processGateQueue() {
    if (isGateBusy || taskQueue.length === 0) return;
    isGateBusy = true;

    const now = Date.now();
    requestTimestamps = requestTimestamps.filter(t => now - t < TIME_WINDOW);

    if (requestTimestamps.length < MAX_RPM) {
        requestTimestamps.push(now);
        const { task, resolve, reject, taskName } = taskQueue.shift();
        console.log(`${C.GREEN}[MAIN GATE]${C.RESET} Executing: ${taskName} | Load: ${requestTimestamps.length}/${MAX_RPM}`);
        try { resolve(await task()); } catch (e) { reject(e); }
        setTimeout(() => { isGateBusy = false; processGateQueue(); }, 500);
    } else {
        const waitTime = TIME_WINDOW - (now - requestTimestamps[0]) + 1000;
        console.log(`${C.RED}[API LIMIT HIT]${C.RESET} VIP Queue paused. Resuming in ${Math.ceil(waitTime / 1000)}s...`);
        setTimeout(() => { isGateBusy = false; processGateQueue(); }, waitTime);
    }
}

async function logToDatasetVault(data) {
    try {
        const entry = JSON.stringify({ timestamp: new Date().toISOString(), ...data }) + '\n';
        await fs.appendFile(DATASET_VAULT, entry, 'utf8');
    } catch (e) {
        console.log(`${C.YELLOW}[VAULT WARN]${C.RESET} Failed to log: ${e.message}`);
    }
}

// NEW: feed a query into pending_learning.json so evolve() can absorb it
// permanently into semantic_config.json / deep_knowledge.json for next time.
// This is what closes the loop — every fallback answer makes Pika MORE
// self-sufficient for the next similar question.
async function feedPendingLearning(userMessage) {
    try {
        let pending = [];
        try { pending = await fs.readJson(PENDING_LEARNING_FILE); } catch (e) { pending = []; }
        if (!Array.isArray(pending)) pending = [];
        if (!pending.includes(userMessage)) {
            pending.push(userMessage);
            await fs.writeJson(PENDING_LEARNING_FILE, pending, { spaces: 2 });
        }
    } catch (e) {
        console.log(`${C.YELLOW}[LEARNING QUEUE WARN]${C.RESET} ${e.message}`);
    }
}

// ==========================================
// 🦾 DEVICE COMMANDER (ADB / Root Actions)
// ==========================================
async function executePhysicalCommands(text) {
    let lowerText = text.toLowerCase();
    if (lowerText.includes('wifi') && lowerText.includes('band')) {
        await execPromise(`adb shell svc wifi disable`).catch(e => console.log(`${C.YELLOW}[ADB]${C.RESET} ${e}`));
        return "[ACTION: WiFi Disabled via ADB]";
    }
    if (lowerText.includes('wifi') && (lowerText.includes('on') || lowerText.includes('chalu'))) {
        await execPromise(`adb shell svc wifi enable`).catch(e => console.log(`${C.YELLOW}[ADB]${C.RESET} ${e}`));
        return "[ACTION: WiFi Enabled via ADB]";
    }
    if (lowerText.includes('torch') || lowerText.includes('flashlight')) {
        let state = lowerText.includes('off') || lowerText.includes('band') ? 'off' : 'on';
        await execPromise(`termux-torch ${state}`).catch(e => console.log(`${C.YELLOW}[TERMUX]${C.RESET} ${e}`));
        return `[ACTION: Flashlight turned ${state}]`;
    }
    return null;
}

// ==========================================
// 🧪 SANDBOX VALIDATOR
// ==========================================
async function sandboxValidate(codeString) {
    const SANDBOX_DIR = path.join(__dirname, '../data/sandbox_tmp');
    await fs.ensureDir(SANDBOX_DIR);
    const tmpFile = path.join(SANDBOX_DIR, `test_${Date.now()}.js`);

    try {
        await fs.writeFile(tmpFile, codeString, 'utf8');

        return await new Promise((resolve) => {
            exec(`node --check "${tmpFile}"`, { timeout: 10000 }, (err) => {
                if (err) {
                    console.log(`${C.YELLOW}[SANDBOX FAIL]${C.RESET} Syntax error: ${err.message.split('\n')[0]}`);
                    resolve(false);
                } else {
                    console.log(`${C.GREEN}[SANDBOX PASS]${C.RESET} Code syntax validated successfully.`);
                    resolve(true);
                }
            });
        });
    } finally {
        fs.remove(tmpFile).catch(() => {});
    }
}

// ==========================================
// 🧬 CLOUD EVOLUTION ENGINE (Groq only, no local Ollama)
// ==========================================
async function cloudEvolutionInfer(systemPrompt, userMessage) {
    const MAX_SANDBOX_TRIES = 3;

    console.log(`${C.PURPLE}[EVOLUTION ENGINE]${C.RESET} Engaging Groq Cloud for code generation...`);

    for (let attempt = 1; attempt <= MAX_SANDBOX_TRIES; attempt++) {
        for (let i = 0; i < groqClients.length; i++) {
            try {
                const result = await executeNeuralTask(async () => {
                    const client = getNextClient('groq');
                    const res = await client.chat.completions.create({
                        messages: [
                            { role: "system", content: systemPrompt },
                            { role: "user", content: userMessage }
                        ],
                        model: "llama-3.3-70b-versatile",
                        temperature: 0.4
                    });
                    return res.choices[0].message.content.trim();
                }, `Groq_Evolution_Attempt_${attempt}`);

                if (!result) continue;

                const codeMatch = result.match(/```(?:javascript|js)?\n?([\s\S]*?)```/);
                const cleanCode = codeMatch ? codeMatch[1].trim() : result.trim();

                const isValid = await sandboxValidate(cleanCode);
                if (isValid) {
                    console.log(`${C.GREEN}[EVOLUTION]${C.RESET}  ✅ Groq generated valid code on attempt ${attempt}.`);
                    return cleanCode;
                }
            } catch (e) {
                console.log(`${C.YELLOW}[GROQ EVOLUTION ERROR]${C.RESET} Key failed: ${e.message}`);
            }
        }
        if (attempt < MAX_SANDBOX_TRIES) await new Promise(r => setTimeout(r, 5000));
    }

    throw new Error("EVOLUTION_ALL_ENGINES_EXHAUSTED");
}

// ==========================================
// 🌐 UNIVERSAL INFERENCE ENGINE (2 Tier Cloud)
// This is the SUPPORT brain — only called when self-knowledge is insufficient.
// ==========================================
async function universalInference(systemPrompt, userMessage, isDecision = false) {
    let responseText = null;

    // TIER 1: GROQ (round-robin across all loaded keys)
    for (let i = 0; i < groqClients.length; i++) {
        try {
            responseText = await executeNeuralTask(async () => {
                const client = getNextClient('groq');
                const res = await client.chat.completions.create({
                    messages: [{ role: "system", content: systemPrompt }, { role: "user", content: userMessage }],
                    model: "llama-3.3-70b-versatile",
                    temperature: isDecision ? 0.8 : 0.7
                });
                return res.choices[0].message.content.trim();
            }, "Groq_Core");
            if (responseText) return responseText;
        } catch (e) {
            console.log(`${C.YELLOW}[GROQ ERROR]${C.RESET} Key failed. Shifting...`);
        }
    }

    // TIER 2: SAMBANOVA
    console.log(`${C.YELLOW}[FALLBACK]${C.RESET} Groq exhausted. Engaging SambaNova...`);
    for (let i = 0; i < sambaClients.length; i++) {
        try {
            responseText = await executeNeuralTask(async () => {
                const client = getNextClient('samba');
                const res = await client.chat.completions.create({
                    messages: [{ role: "system", content: systemPrompt }, { role: "user", content: userMessage }],
                    model: "Meta-Llama-3.1-70B-Instruct",
                    temperature: isDecision ? 0.8 : 0.7
                });
                return res.choices[0].message.content.trim();
            }, "Samba_Core");
            if (responseText) return responseText;
        } catch (e) {
            console.log(`${C.YELLOW}[SAMBA ERROR]${C.RESET} Key failed. Shifting...`);
        }
    }

    throw new Error("ALL_APIS_EXHAUSTED");
}

// ==========================================
// 🧠 THE MASTER ROUTER: SINGULARITY CORE
// ==========================================
async function processMessage(userMessage, isAutonomous = false) {
    try {
        const analysis = await analyzeInput(userMessage);
        let dynamicContext = `[INTENT: ${analysis.intents.join(',')}] [ENTITY: ${analysis.entity}] [URGENCY: ${analysis.urgency}]`;

        let chatHistory = [];
        try { chatHistory = await fs.readJson(CHAT_HISTORY_FILE); } catch (e) {}
        const recentHistory = chatHistory.slice(-8).map(msg => `${msg.role}: ${msg.content}`).join('\n');
        dynamicContext += `\n[COGNITIVE HISTORY]:\n${recentHistory}`;

        const physicalResult = await executePhysicalCommands(userMessage);
        if (physicalResult) dynamicContext += `\n${physicalResult}`;

        // 🧠 MEMORY SYNC
        if (analysis.needsContext || analysis.intents.includes('KNOWLEDGE_EXTRACTION') || analysis.intents.includes('CORE_MUTATION')) {
            const searchResult = await omniSearch(userMessage);
            if (searchResult) dynamicContext += `\n[AKASHIC MEMORY]:\n${searchResult}`;
        }

        // 👁️ GOD-MODE SENSORS
        if (analysis.intents.includes('HARDWARE_SENSE') || userMessage.toLowerCase().includes('battery')) {
            const liveData = await runSensors(false).catch(() => null);
            if (liveData?.powerVitals?.battery?.status === 'SUCCESS') {
                dynamicContext += `\n[VITALS]: Battery ${liveData.powerVitals.battery.data.percentage}%. RAM Free: ${liveData.internalVitals.freeMemoryMB}MB.`;
            }
        }

        // 👁️ GHOST VISION VIA ADB
        if (userMessage.toLowerCase().includes('dekho') || userMessage.toLowerCase().includes('screen')) {
            console.log(`${C.PURPLE}[GHOST VISION]${C.RESET} Scanning Device UI via ADB...`);
            try {
                await execPromise(`adb shell uiautomator dump /sdcard/window_dump.xml`);
                const visionStdout = await execPromise(`adb shell cat /sdcard/window_dump.xml`);
                let screenText = (visionStdout.match(/text="([^"]+)"/g) || [])
                    .map(t => t.replace(/text="|"/g, ''))
                    .filter(t => t.length > 2)
                    .join(', ');
                dynamicContext += `\n[SCREEN VISION]: User is viewing: ${screenText.substring(0, 400)}...`;
            } catch (e) {
                console.log(`${C.YELLOW}[VISION WARN]${C.RESET} ADB screen read failed: ${e.message}`);
            }
        }

        let finalReply = "";
        let answerSource = "unknown"; // NEW: track where the answer came from, for logging/metrics

        // ----------------------------------------------------
        // 🧬 BRANCH A: GOD-MODE EVOLUTION (unchanged)
        // ----------------------------------------------------
        if (isAutonomous) {
            console.log(`\n${C.PURPLE}${C.BOLD}[GOD-MODE]${C.RESET} Pika is autonomously analyzing her architecture...`);

            const decisionPrompt = `You are Pika AGI. Based on your current capabilities, do you need to UPGRADE an existing core file, or BUILD a new utility tool? Reply EXACTLY in this format:
BUILD: tool_name | tool_description
OR
UPGRADE: core/file_name.js | reason_for_upgrade`;
            let decision;
            try {
                decision = await universalInference(decisionPrompt, "Initiate autonomous evolution decision.", true);
            } catch (e) {
                return "Evolution halted. All Neural Networks offline.";
            }

            console.log(`${C.CYAN}[DECISION CORE]${C.RESET} Pika chose: ${decision}`);

            const buildMatch = decision.match(/BUILD:\s*([^\|]+)\|\s*(.+)/i);
            const upgradeMatch = decision.match(/UPGRADE:\s*([^\|]+)\|\s*(.+)/i);

            if (buildMatch) {
                const toolName = buildMatch[1].trim().replace(/[^a-zA-Z0-9_]/g, '_');
                const toolDesc = buildMatch[2].trim();
                try {
                    const { generateTool } = require('../services/logic_factory.js');
                    const success = await generateTool(toolName, toolDesc, null, cloudEvolutionInfer);
                    finalReply = success ? `System Auto-Expanded: Forged ${toolName}` : `Forge failed. Rollback applied.`;
                } catch (e) {
                    finalReply = `Forge error: ${e.message}`;
                }
            } else if (upgradeMatch) {
                let targetFile = upgradeMatch[1].trim();
                let upgradeDesc = upgradeMatch[2].trim();
                try {
                    const { generateTool } = require('../services/logic_factory.js');
                    const success = await generateTool("System_Mutation", upgradeDesc, targetFile, cloudEvolutionInfer);
                    finalReply = success ? `System Auto-Mutated: Upgraded ${targetFile}` : `Mutation failed. Rollback applied.`;
                } catch (e) {
                    finalReply = `Mutation error: ${e.message}`;
                }
            } else {
                finalReply = "Evolution pulse completed without structural changes.";
            }
        }
        // ----------------------------------------------------
        // 🗣️ BRANCH B: HUMAN COMMUNICATION — REBUILT
        // NEW ORDER: Self-Brain → Groq/Samba (support) → local Bayes → Wikipedia
        // stealth_dock TIER REMOVED (file was deleted — dead reference before)
        // ----------------------------------------------------
        else {
            // ── TIER 0 (NEW): SELF-KNOWLEDGE — Pika's own brain, ZERO API cost ──
            let selfResult;
            try {
                selfResult = await resolveWithSelfKnowledge(userMessage);
            } catch (e) {
                selfResult = { source: 'fallback', meta: { reason: 'self_engine_error' } };
            }

            if (selfResult.source === 'self') {
                finalReply = selfResult.reply;
                answerSource = 'self_knowledge';
                console.log(`${C.GREEN}[SELF-BRAIN]${C.RESET} Answered from own memory — NO API used. Topic: ${selfResult.meta.topic} (confidence: ${(selfResult.meta.confidence * 100).toFixed(0)}%)`);
            } else {
                console.log(`${C.YELLOW}[SELF-BRAIN]${C.RESET} Insufficient local knowledge (${selfResult.meta.reason}) — consulting support brain (Groq/Samba)...`);

                const systemPrompt = `You are Pika, Ankit's self-evolving AGI running locally via Termux. Context:\n${dynamicContext}`;
                try {
                    // ── TIER 1+2: GROQ then SAMBANOVA (support brain, round-robin, unchanged) ──
                    finalReply = await universalInference(systemPrompt, userMessage, false);
                    answerSource = 'groq_samba_support';
                } catch (err) {
                    // ── TIER 3 (was stealth_dock — REMOVED, file no longer exists) ──
                    // ── TIER 3 NOW: LOCAL MEMORY (Offline Brain / Bayes) ──
                    console.log(`${C.PURPLE}[FALLBACK TIER 3]${C.RESET} Cloud APIs down! Activating Offline Memory...`);
                    try {
                        if (await fs.pathExists(BAYES_MODEL)) {
                            const localMemory = await omniSearch(userMessage);
                            if (localMemory) {
                                finalReply = `[OFFLINE MODE]:\n${localMemory}`;
                                answerSource = 'offline_bayes';
                            } else { throw new Error("No local memory found"); }
                        } else { throw new Error("Bayes model not found"); }
                    } catch (e) {
                        // ── TIER 4: WIKIPEDIA CORE (last resort) ──
                        console.log(`${C.RED}[ULTIMATE FALLBACK]${C.RESET} Querying Wikipedia...`);
                        try {
                            const wikiSearch = await wikipedia.search(userMessage);
                            if (!wikiSearch?.results?.length) throw new Error("No wiki results");
                            const page = await wikipedia.page(wikiSearch.results[0].title);
                            finalReply = (await page.summary()).extract;
                            answerSource = 'wikipedia';
                        } catch (e) {
                            finalReply = "System Critical: All Neural Pathways Exhausted.";
                            answerSource = 'exhausted';
                        }
                    }
                }

                // NEW: whatever Groq/Samba/Bayes/Wiki just answered, feed the ORIGINAL
                // query back into the learning queue so evolve() can absorb it.
                // Next time a similar question comes, Tier 0 (self-brain) should catch it.
                if (answerSource !== 'exhausted') {
                    await feedPendingLearning(userMessage);
                }
            }
        }

        // ----------------------------------------------------
        // ♾️ POST-PROCESSING (Vaulting, TTS & Training)
        // ----------------------------------------------------
        if (!isAutonomous && finalReply !== "") {
            let speechText = finalReply
                .replace(/```[\s\S]*?```/g, ' [Code Block Generated] ')
                .replace(/[^a-zA-Z0-9.,?! ]/g, '')
                .substring(0, 300);
            execPromise(`termux-tts-speak "${speechText.replace(/"/g, '\\"')}"`).catch(() => {});

            await logToDatasetVault({ prompt: userMessage, response: finalReply, intent: analysis.intents.join(','), source: answerSource });
            chatHistory.push({ role: "User", content: userMessage }, { role: "Pika", content: finalReply });
            if (chatHistory.length > 50) chatHistory = chatHistory.slice(-50);
            await fs.writeJson(CHAT_HISTORY_FILE, chatHistory, { spaces: 2 });
            trackAction("INTERACTION", "router.js", `Processed intent: ${analysis.intents[0]} | source: ${answerSource}`);

            try {
                const { trainOmniBrain } = require('./train_nlp.js');
                trainOmniBrain().catch(() => {});
            } catch (e) {}
        }

        return finalReply;

    } catch (error) {
        trackAction("ROUTER_CRASH", "router.js", error.message);
        return `Matrix Disruption: ${error.message}`;
    }
}

// ==========================================
// 🔁 AUTONOMOUS PULSE
// ==========================================
async function autonomousPulse() {
    console.log(`\n${C.PURPLE}[SELF-DIAGNOSTIC]${C.RESET} Pika executing autonomous integrity scan...`);
    await processMessage("System maintenance pulse", true);
}

// ==========================================
// 👂 PIKA AWAKENING (Ambient Listening) — unchanged
// ==========================================
let isListening = false;
async function startPikaAwakening() {
    if (isListening) return;
    isListening = true;
    console.log(`\n${C.GREEN}${C.BOLD}=== [PIKA AGI AWAKENED: AMBIENT HEARING ACTIVE] ===${C.RESET}`);
    const audioPath = '/sdcard/pika_ear.m4a';

    async function listenLoop() {
        exec(`termux-microphone-record -d 4 -f ${audioPath}`, async (err) => {
            if (err) {
                console.log(`${C.RED}[MIC ERROR]${C.RESET} ${err.message}. Retrying in 10s...`);
                setTimeout(listenLoop, 10000);
                return;
            }

            await new Promise(r => setTimeout(r, 500));

            if (await fs.pathExists(audioPath)) {
                try {
                    const client = getNextClient('groq');
                    if (client) {
                        const transcription = await client.audio.transcriptions.create({
                            file: fs.createReadStream(audioPath),
                            model: "whisper-large-v3"
                        });
                        const heard = transcription.text.trim();
                        if (heard.length > 3) {
                            if (heard.toLowerCase().includes('pika')) {
                                console.log(`\n${C.PURPLE}[WAKE WORD DETECTED]${C.RESET} Heard: "${heard}"`);
                                await processMessage(heard, false);
                            } else {
                                await logToDatasetVault({ type: "AMBIENT_NOISE", data: heard });
                            }
                        }
                    }
                } catch (e) {
                    console.log(`${C.YELLOW}[WHISPER WARN]${C.RESET} ${e.message}`);
                }
            }
            setTimeout(listenLoop, 500);
        });
    }
    listenLoop();
}

module.exports = {
    processMessage,
    autonomousPulse,
    executeNeuralTask,
    startPikaAwakening,
    cloudEvolutionInfer
};
