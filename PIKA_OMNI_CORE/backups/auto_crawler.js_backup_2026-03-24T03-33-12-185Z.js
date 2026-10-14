const fs = require('fs-extra');
const path = require('path');
const Groq = require('groq-sdk');
const { OpenAI } = require('openai'); // SambaNova Neural Interface
require('dotenv').config();

const { readMemory, saveMemory } = require('../core/memory_manager.js');
const { runStealthDock } = require('./stealth_dock.js');
const { executeNeuralTask } = require('../core/router.js'); // Global Queue Integration

// ==========================================
// 🔄 DYNAMIC API ENGINE (REVERSE ROTATION)
// ==========================================
const sambaClients = [];
const groqClients = [];

let s = 1;
while(process.env[`SAMBA_${s}`]) {
    sambaClients.push(new OpenAI({
        apiKey: process.env[`SAMBA_${s}`].trim(),
        baseURL: "https://api.sambanova.ai/v1"
    }));
    s++;
}

let g = 1;
while(process.env[`GROQ_${g}`]) {
    groqClients.push(new Groq({
        apiKey: process.env[`GROQ_${g}`].trim()
    }));
    g++;
}

// Trackers starting from the last index (Reverse Mode)
let currentSambaTracker = Math.max(0, sambaClients.length - 1);
let currentGroqTracker = Math.max(0, groqClients.length - 1);

function getSamba() {
    if (sambaClients.length === 0) throw new Error("CRITICAL: SAMBA_ keys not found in .env!");
    const client = sambaClients[currentSambaTracker];
    console.log(`\x1b[36m[NETWORK SHIFT]\x1b[0m Crawler routing through SambaNova Key #${currentSambaTracker + 1} (Reverse Mode)`);
    currentSambaTracker = (currentSambaTracker - 1 + sambaClients.length) % sambaClients.length;
    return client;
}

function getGroq() {
    if (groqClients.length === 0) throw new Error("CRITICAL: GROQ_ keys not found in .env!");
    const client = groqClients[currentGroqTracker];
    console.log(`\x1b[36m[NETWORK SHIFT]\x1b[0m Crawler routing through Groq Key #${currentGroqTracker + 1} (Reverse Mode)`);
    currentGroqTracker = (currentGroqTracker - 1 + groqClients.length) % groqClients.length;
    return client;
}

// ==========================================
// 🎨 TERMINAL MATRICES
// ==========================================
const C = {
    CYAN: "\x1b[38;5;51m",
    PURPLE: "\x1b[38;5;213m",
    GREEN: "\x1b[38;5;82m",
    RED: "\x1b[38;5;196m",
    YELLOW: "\x1b[38;5;226m",
    RESET: "\x1b[0m"
};

// Dynamic Speed configuration
let baseInterval = 2;
let currentInterval = baseInterval;
let crawlerTimer = null;

// ==========================================
// 🧠 NEURAL KNOWLEDGE EXTRACTION
// ==========================================
async function structureKnowledge(topic, rawText) {
    console.log(`${C.PURPLE}[NEURAL CORE]${C.RESET} Analyzing '${topic}' and extracting pure intelligence...`);

    const prompt = `You are the autonomous learning engine of Pika AGI.
Analyze the following raw internet text about the topic: "${topic}".
Extract the core intelligence and structure it EXACTLY in this JSON format. Ignore conversational text.
{
  "definition": "A clear explanation of the technology in professional English.",
  "core_concepts": ["pure english tech term 1", "pure english tech term 2"],
  "use_case": "Real-world application in English."
}

CRITICAL: Return ONLY the JSON object. Do not include any markdown formatting or extra text.
Raw Text: ${rawText}`;

    try {
        let jsonStr = await executeNeuralTask(async () => {
            const response = await getSamba().chat.completions.create({
                messages: [{ role: "system", content: prompt }],
                model: "Meta-Llama-3.1-8B-Instruct", 
                temperature: 0.1, 
                max_tokens: 500
            });
            return response.choices[0].message.content.trim();
        }, "Crawler_Knowledge_Extraction");

        const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
        } else {
            throw new Error("No JSON structure detected in Neural response.");
        }

    } catch (err) {
        console.log(`${C.YELLOW}[STRUCTURING FAILED]${C.RESET} Neural extraction aborted. Error: ${err.message}`);
        return { definition: "Analysis failed.", core_concepts: [], use_case: "Unknown" };
    }
}

// ==========================================
// 🚀 THE MAIN CRAWLER ENGINE
// ==========================================
async function startAutonomousEvolution() {
    if (!global.isSleeping) {
        console.log(`${C.YELLOW}[CRAWLER PAUSED]${C.RESET} Architect is currently active. Evolution engine standing by.`);
        return;
    }

    console.log(`\n${C.CYAN}[EVOLUTION ENGINE]${C.RESET} Autonomous Web Crawler Booting Up...`);

    let deepK = await readMemory('deep_knowledge.json') || {};
    let pending = await readMemory('pending_learning.json') || [];

    // 🛡️ THE ULTIMATE FIX: Graceful Idle Mode instead of Infinite Loop
    if (!Array.isArray(pending) || pending.length === 0) {
        console.log(`${C.YELLOW}[SYSTEM IDLE]${C.RESET} Curiosity Queue is empty or corrupted. Waiting for Architect to provide new valid JSON topics.`);
        return; // Halts the function here. Prevents overwriting and infinite loops.
    }

    let currentTopic = pending.shift();

    if (deepK[currentTopic]) {
        console.log(`${C.PURPLE}[SKIP]${C.RESET} Pika has already mastered: ${currentTopic}`);
        await saveMemory('pending_learning.json', pending);
        return;
    }

    console.log(`${C.CYAN}[HUNTING]${C.RESET} Researching: ${C.YELLOW}${currentTopic}${C.RESET}`);

    let knowledgeText = await runStealthDock(currentTopic);

    const isApiError = knowledgeText && (knowledgeText.startsWith('Error') || knowledgeText.includes('API_LIMIT_EXCEEDED') || knowledgeText.includes('429 Unauthorized'));

    if (knowledgeText && !isApiError) {
        currentInterval = baseInterval;

        let structuredData = await structureKnowledge(currentTopic, knowledgeText);
        structuredData.learned_on = new Date().toISOString();
        deepK[currentTopic] = structuredData;

        let newConcepts = structuredData.core_concepts || [];
        let addedCount = 0;

        if (Array.isArray(newConcepts)) {
            newConcepts.forEach(concept => {
                if (concept && typeof concept === 'string' && concept.length > 2) {
                    if (!deepK[concept] && !pending.includes(concept)) {
                        pending.push(concept);
                        addedCount++;
                    }
                }
            });
        }

        console.log(`${C.GREEN}[DIGESTED]${C.RESET} '${currentTopic}' successfully integrated into Neural Core!`);
        console.log(`${C.PURPLE}[SYNAPSES FIRED]${C.RESET} ${addedCount} new pure tech concepts added to the learning queue.`);

        await saveMemory('deep_knowledge.json', deepK);
        await saveMemory('pending_learning.json', pending);

    } else {
        console.log(`${C.RED}[DEAD END OR LIMIT HIT]${C.RESET} Data extraction failed for '${currentTopic}'.`);

        if (isApiError) {
            currentInterval = Math.min(currentInterval * 2, 10);
            console.log(`${C.YELLOW}[SPEED SHIFT]${C.RESET} API Limit detected. Engaging backoff protocol...`);
            pending.unshift(currentTopic);
            await saveMemory('pending_learning.json', pending);
        } else {
            console.log(`${C.YELLOW}[MEMORY CLEANUP]${C.RESET} Invalid concept deleted permanently.`);
            await saveMemory('pending_learning.json', pending);
        }
    }
}

// ==========================================
// 🕒 THE RECURSIVE DYNAMIC LOOP
// ==========================================
function loopStep() {
    startAutonomousEvolution().finally(() => {
        crawlerTimer = setTimeout(loopStep, currentInterval * 60 * 1000);
    });
}

function runInfiniteLoop(intervalMinutes) {
    baseInterval = intervalMinutes;
    currentInterval = baseInterval;
    console.log(`\n${C.GREEN}[AUTONOMY ACTIVE]${C.RESET} Crawler Engine primed. Base cycle interval: ${baseInterval} minutes.`);
    loopStep();
}

// Added error handling for unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
    console.log(`\x1b[38;5;196m[UNHANDLED REJECTION]${C.RESET} Reason: ${reason}`);
});

// Added error handling for uncaught exceptions
process.on('uncaughtException', (err) => {
    console.log(`\x1b[38;5;196m[UNCAUGHT EXCEPTION]${C.RESET} Error: ${err.message}`);
});

// Improved error handling for memory operations
async function safeReadMemory(filename) {
    try {
        return await readMemory(filename);
    } catch (err) {
        console.log(`\x1b[38;5;196m[MEMORY READ ERROR]${C.RESET} Error reading ${filename}: ${err.message}`);
        return null;
    }
}

async function safeSaveMemory(filename, data) {
    try {
        await saveMemory(filename, data);
    } catch (err) {
        console.log(`\x1b[38;5;196m[MEMORY SAVE ERROR]${C.RESET} Error saving ${filename}: ${err.message}`);
    }
}

// Replaced readMemory and saveMemory with safeReadMemory and safeSaveMemory
async function startAutonomousEvolution() {
    if (!global.isSleeping) {
        console.log(`${C.YELLOW}[CRAWLER PAUSED]${C.RESET} Architect is currently active. Evolution engine standing by.`);
        return;
    }

    console.log(`\n${C.CYAN}[EVOLUTION ENGINE]${C.RESET} Autonomous Web Crawler Booting Up...`);

    let deepK = await safeReadMemory('deep_knowledge.json') || {};
    let pending = await safeReadMemory('pending_learning.json') || [];

    // ... rest of the code remains the same ...
}

module.exports = { startAutonomousEvolution, runInfiniteLoop };