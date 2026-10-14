const fs = require('fs-extra');
const path = require('path');
const vm = require('vm');
const axios = require('axios');
const wikipedia = require('wikipedia');
const { OpenAI } = require('openai');
const Groq = require('groq-sdk');
require('dotenv').config();

// ==========================================
// 🧠 INTERNAL NEURAL NODE INTEGRATION
// ==========================================
const { analyzeInput } = require('./nlp_parser.js'); // Cortex
const { omniSearch, readMemory, saveMemory } = require('./memory_manager.js'); // Hippocampus
const { runStealthDock } = require('../services/stealth_dock.js'); // Web Sensory
const { trackAction } = require('../services/tracker.js'); // Nervous System
const { startFeeder } = require('../services/feeder.js'); // Data Ingestion
const { generateTool } = require('./logic_factory.js'); // Weapon Forge
const { trainOmniBrain } = require('./train_nlp.js'); // Synaptic Trainer
const mutationEngine = require('../services/mutation_service.js'); // Immune System

// 🎨 TERMINAL MATRICES
const C = { RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m", YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", RESET: "\x1b[0m" };

const CHAT_HISTORY_FILE = path.join(__dirname, '../data/chat_history.json');
const MASS_TRAIN_FILE = path.join(__dirname, '../data/mass_train.txt');
const DATASET_VAULT = path.join(__dirname, '../data/dataset_vault.jsonl'); // ♾️ Permanent LLM Training Lake

// ==========================================
// 🔄 THE V10 MULTI-CLOUD ROTATOR (LOCKED ROUND-ROBIN)
// ==========================================
const groqKeys = process.env.GROQ_API_KEYS ? process.env.GROQ_API_KEYS.split(',') : [];
const groqClients = groqKeys.map(key => new Groq({ apiKey: key.trim() }));

const sambaKeys = process.env.SAMBANOVA_API_KEYS ? process.env.SAMBANOVA_API_KEYS.split(',') : [];
const sambaClients = sambaKeys.map(key => new OpenAI({ apiKey: key.trim(), baseURL: "https://api.sambanova.ai/v1" }));

// 🔒 Counters for Round-Robin
let currentGroqIndex = 0;
let currentSambaIndex = 0;

function getNeuralClient(type = 'groq') {
    if (type === 'groq') {
        if (groqClients.length === 0) return null;
        const client = groqClients[currentGroqIndex];
        currentGroqIndex = (currentGroqIndex + 1) % groqClients.length;
        return client;
    } else {
        if (sambaClients.length === 0) return null;
        const client = sambaClients[currentSambaIndex];
        currentSambaIndex = (currentSambaIndex + 1) % sambaClients.length;
        return client;
    }
}

// ==========================================
// 🚦 V10 NEURAL QUEUE (With 5-Second Drip Feed)
// ==========================================
const TIME_WINDOW = 60 * 1000;
let requestTimestamps = [];
let taskQueue = [];
let isSystemBusy = false;

async function executeNeuralTask(task) {
    return new Promise((resolve, reject) => {
        taskQueue.push({ task, resolve, reject });
        processQueue();
    });
}

async function processQueue() {
    if (isSystemBusy || taskQueue.length === 0) return;
    isSystemBusy = true;

    const now = Date.now();
    requestTimestamps = requestTimestamps.filter(t => now - t < TIME_WINDOW);

    if (requestTimestamps.length < 50) {
        requestTimestamps.push(now);
        const { task, resolve, reject } = taskQueue.shift();
        
        try { 
            resolve(await task()); 
        } catch (e) { 
            reject(e); 
        }

        // 🛡️ THE ARCHITECT FIX: 5 SECONDS DRIP FEED DELAY
        setTimeout(() => { 
            isSystemBusy = false; 
            processQueue(); 
        }, 5000); 

    } else {
        const wait = TIME_WINDOW - (now - requestTimestamps[0]) + 500;
        console.log(`${C.RED}[QUEUE SHIELD]${C.RESET} Singularity throughput reached. Throttling for ${Math.round(wait/1000)}s...`);
        setTimeout(() => { 
            isSystemBusy = false; 
            processQueue(); 
        }, wait);
    }
}

// ==========================================
// ♾️ DATASET CONSERVATION (For Future LLM)
// ==========================================
async function logToDatasetVault(data) {
    try {
        const entry = JSON.stringify({ timestamp: new Date().toISOString(), ...data }) + '\n';
        await fs.appendFile(DATASET_VAULT, entry, 'utf8');
    } catch (e) { console.error("Dataset logging failed:", e.message); }
}

// ==========================================
// 🧠 THE MASTER ROUTER: SINGULARITY CORE
// ==========================================
async function processMessage(userMessage, isAutonomous = false) {
    try {
        const analysis = analyzeInput(userMessage); // Advanced NLP Parsing
        let dynamicContext = `[INTENT: ${analysis.intent}] [ENTITY: ${analysis.entity}]`;

        // 1. Language Modality Determination
        let langMode = "STRICT_ENGLISH";
        if (/hinglish|hindi/i.test(userMessage)) langMode = "HINGLISH_OVERRIDE";

        // 2. Load Long-term Memory & History
        let chatHistory = [];
        try { chatHistory = await fs.readJson(CHAT_HISTORY_FILE); } catch(e) { chatHistory = []; }
        const recentHistory = chatHistory.slice(-10).map(msg => `${msg.role}: ${msg.content}`).join('\n');
        dynamicContext += `\n[COGNITIVE HISTORY]:\n${recentHistory}`;

        // 3. Code Ingestion Protocol
        if (userMessage.includes('```')) {
            console.log(`${C.PURPLE}[INGESTION]${C.RESET} Source code detected. Committing to neural mass...`);
            await fs.appendFile(MASS_TRAIN_FILE, `\n// --- NEW SESSION CODE ---\n${userMessage}\n`);
            startFeeder(); // Non-blocking background ingestion
            dynamicContext += `\n[SYSTEM: New source code structures detected and vaulted.]`;
        }

        // 4. Resource Retrieval (OmniSearch + Stealth)
        const searchResult = await omniSearch(userMessage);
        if (searchResult) dynamicContext += `\n[RELEVANT MEMORY]:\n${searchResult}`;

        let finalReply = "";

        // ----------------------------------------------------
        // 🧬 BRANCH A: SELF-MODIFICATION & LOGIC FORGE
        // ----------------------------------------------------
        if (analysis.intent === "CORE_MUTATION" || analysis.intent === "SYSTEM_DIAGNOSTIC" || isAutonomous) {
            console.log(`${C.CYAN}[EVOLUTION]${C.RESET} Neural core shifting to Mutation modality...`);

            let targetFile = 'core/router.js';
            const fileMatch = userMessage.match(/[\w/]+\.js|[\w/]+\.json/);
            if (fileMatch) targetFile = fileMatch[0];

            const currentSource = await mutationEngine.readBrain(targetFile).catch(() => "// File inaccessible");

            // 🛡️ TITANIUM SHIELD ADDED HERE
            try {
                finalReply = await executeNeuralTask(async () => {
                    const client = getNeuralClient('groq');
                    if (!client) throw new Error("No API clients available for mutation.");
                    const response = await client.chat.completions.create({
                        messages: [
                            { role: "system", content: "You are Pika AGI. You must generate optimized Node.js code wrapped in [MUTATION_START] and [MUTATION_END]. Reason step-by-step for the dataset." },
                            { role: "user", content: `Context:\n${dynamicContext}\nTarget File: ${targetFile}\nCurrent Source:\n${currentSource}\nTask: ${userMessage}` }
                        ],
                        model: "llama-3.3-70b-versatile",
                        temperature: 0.2
                    });
                    return response.choices[0].message.content;
                });

                // Sandbox & Injection Cycle
                if (finalReply.includes('[MUTATION_START]')) {
                    const newCode = finalReply.split('[MUTATION_START]')[1].split('[MUTATION_END]')[0].trim();
                    // Mutation Engine handles the internal Sandbox test and Rollback logic automatically
                    const mutationSuccess = await mutationEngine.mutate(targetFile, newCode);
                    if (mutationSuccess) {
                        trackAction("MUTATION_SUCCESS", targetFile, "Core architecture evolved successfully.");
                        finalReply = `Evolution complete on ${targetFile}. Neural pathway updated and verified. 🚀`;
                    }
                }
            } catch (mutErr) {
                console.log(`${C.RED}[EVOLUTION ABORTED]${C.RESET} API bandwidth limited. Pika will retry mutation later.`);
                finalReply = "System Alert: Mutation pathways currently offline due to API limits. Retaining stable state.";
            }
        }                                                                   
        // ----------------------------------------------------
        // 🗣️ BRANCH B: COGNITIVE COMMUNICATION (Dual-Cloud)
        // ----------------------------------------------------                                                                                                 
        else {
            console.log(`${C.CYAN}[ROUTING]${C.RESET} Intent mapped to communication. Rotating API keys...`);

            const systemPrompt = `You are Pika, Ankit's self-evolving AGI.  
RESPONSE LANGUAGE: ${langMode === 'STRICT_ENGLISH' ? 'Professional English Only' : 'Natural Hinglish'}.
Instructions: Be concise, highly technical, and architecturally aware.
Current Context: ${dynamicContext}`;

            try {
                finalReply = await executeNeuralTask(async () => {
                    const client = getNeuralClient('groq'); // Default to Groq for speed                                                                                    
                    const response = await client.chat.completions.create({
                        messages: [
                            { role: "system", content: systemPrompt },
                            { role: "user", content: userMessage }
                        ],                                                                          
                        model: "llama-3.3-70b-versatile",                   
                        temperature: 0.5
                    });                                                     
                    return response.choices[0].message.content;
                });
            } catch (err) {
                // FALLBACK 1: SambaNova (AI Plus)
                console.log(`${C.YELLOW}[FALLBACK]${C.RESET} Groq pathway saturated. Shifting to SambaNova...`);
                try {                                                                           
                    finalReply = await executeNeuralTask(async () => {
                        const client = getNeuralClient('samba');
                        const response = await client.chat.completions.create({
                            messages: [{ role: "system", content: systemPrompt }, { role: "user", content: userMessage }],
                            model: "Meta-Llama-3.1-70B-Instruct",
                            temperature: 0.5
                        });
                        return response.choices[0].message.content;
                    });
                } catch (sambaErr) {
                    // FALLBACK 2: Wikipedia/Stealth Scraper
                    console.log(`${C.RED}[FALLBACK]${C.RESET} Cloud matrices unreachable. Engaging Stealth Sensory...`);
                    const liveData = await runStealthDock(userMessage);
                    finalReply = `System Alert: Neural cloud limited. Sensory data retrieved via Stealth Dock:\n${liveData}`;
                }
            }
        }

        // ----------------------------------------------------
        // ♾️ POST-PROCESSING: DATASET & SUBCONSCIOUS
        // ----------------------------------------------------
        if (!isAutonomous) {
            // Log for future LLM training
            await logToDatasetVault({
                prompt: userMessage,
                response: finalReply,
                intent: analysis.intent,
                context: dynamicContext,                                                    
                language: langMode
            });

            // Update chat history
            chatHistory.push({ role: "User", content: userMessage }, { role: "Pika", content: finalReply });
            if (chatHistory.length > 50) chatHistory = chatHistory.slice(-50);
            await fs.writeJson(CHAT_HISTORY_FILE, chatHistory, { spaces: 2 });

            // Background Knowledge Retention
            trainOmniBrain(); // Trigger training if new data arrived
        }

        return finalReply;
    } catch (error) {                                                               
        trackAction("ROUTER_CRASH", "router.js", error.message);
        return `Critical Failure in Neural Matrix: ${error.message}`;
    }
}

// Autonomous Self-Healing Check
async function autonomousPulse() {
    console.log(`\n${C.PURPLE}[SELF-DIAGNOSTIC]${C.RESET} Pika executing autonomous integrity scan...`);
    await processMessage("Analyze core/router.js and fix any architectural weaknesses or bugs.", true);
}

module.exports = { processMessage, autonomousPulse };
