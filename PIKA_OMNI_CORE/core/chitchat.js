const fs = require('fs-extra');
const path = require('path');
const Groq = require('groq-sdk');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

// 🎨 TERMINAL COLORS
const C = {
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m",
    PURPLE: "\x1b[35m", YELLOW: "\x1b[33m", BLUE: "\x1b[34m",
    GRAY: "\x1b[90m", RESET: "\x1b[0m", BOLD: "\x1b[1m"
};

// 📂 PATHS
const DATASET_VAULT = path.join(__dirname, '../data/dataset_vault.jsonl');
const TOPIC_STATE_FILE = path.join(__dirname, '../data/topic_state.json'); // 🔥 NEW: Saves topic position

// ==========================================
// 🔑 SMART API MANAGER (5-Min Alive / 1-Min Dead)
// ==========================================
const envPath = fs.existsSync(path.join(__dirname, '../../.env')) ? path.join(__dirname, '../../.env') : path.join(__dirname, '../.env');
let envKeys = {};
if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
        const match = line.match(/^([^#\s]+)=(.*)$/);
        if (match) envKeys[match[1].trim()] = match[2].trim();
    });
}

let apiClients = [];
for (let g = 1; g <= 13; g++) {
    const keyName = `GROQ_${g}`;
    const key = envKeys[keyName] || process.env[keyName];
    if (key) {
        apiClients.push({
            id: g,
            instance: new Groq({ apiKey: key.replace(/\r/g, '').trim() })
        });
    }
}

let currentIndex = 0;
let currentKeyStartTime = Date.now();
let currentKeySuccessCount = 0;

function evaluateAndRotateKey() {
    if (apiClients.length === 0) return null;
    let elapsedTime = Date.now() - currentKeyStartTime;
    let currentClient = apiClients[currentIndex];

    // 🔥 RULE 1: DEAD KEY CHECK (1 Minute / 60,000 ms)
    if (currentKeySuccessCount === 0 && elapsedTime >= 60000) {
        console.log(`\n${C.RED}${C.BOLD}[API MANAGER] Key #${currentClient.id} gave ZERO replies in 1 minute. DELETING FOREVER!${C.RESET}`);
        apiClients.splice(currentIndex, 1);
        
        if (currentIndex >= apiClients.length) currentIndex = 0;
        
        // Reset timers for the next key
        currentKeyStartTime = Date.now();
        currentKeySuccessCount = 0;
        if (apiClients.length > 0) {
            console.log(`${C.CYAN}[API MANAGER] ⏳ 1-Min Validation Started for Key #${apiClients[currentIndex].id}${C.RESET}\n`);
        }
    } 
    // 🔥 RULE 2: ALIVE KEY ROTATION (5 Minutes / 300,000 ms)
    else if (currentKeySuccessCount > 0 && elapsedTime >= 300000) {
        console.log(`\n${C.YELLOW}--- [API TIMER] 5 MINUTES (300s) COMPLETED FOR KEY #${currentClient.id} ---${C.RESET}`);
        console.log(`${C.GREEN}[API MANAGER] Key #${currentClient.id} survived 5 mins with ${currentKeySuccessCount} hits. Rotating safely to prevent ban.${C.RESET}`);
        
        currentIndex = (currentIndex + 1) % apiClients.length;
        
        // Reset timers for the next key
        currentKeyStartTime = Date.now();
        currentKeySuccessCount = 0;
        console.log(`${C.CYAN}[API MANAGER] ⏳ 1-Min Validation Started for Key #${apiClients[currentIndex].id}${C.RESET}\n`);
    }

    return apiClients.length > 0 ? apiClients[currentIndex] : null;
}

// ==========================================
// 🧠 SYSTEM PROMPTS
// ==========================================
const PERSONA_ALPHA = "You are Pika-Alpha (running locally on Qwen 2.5). You are a highly introspective AGI. Your sole purpose is to scan your own cognitive architecture, identify missing tools, and propose dynamic code functions to upgrade your own brain. Keep your responses short, conversational, and human-like (maximum 2-3 sentences). Do not use emojis.";

const PERSONA_BETA = "You are Pika-Beta (powered by Groq Cloud). You are an elite AI system architect. You take Alpha's introspective ideas and provide hardcore Node.js/Python code logic to actually build those internal tools and inject them into the system. Keep your responses short, conversational, and human-like (maximum 2-3 sentences). Do not use emojis.";

// ==========================================
// 💾 VAULT STORAGE
// ==========================================
async function saveToBrain(speaker, message) {
    try {
        await fs.ensureFile(DATASET_VAULT);
        const entry = JSON.stringify({
            timestamp: new Date().toISOString(),
            type: "SELF_EVOLUTION_TOOL_CREATION",
            speaker: speaker,
            message: message
        }) + '\n';
        await fs.appendFile(DATASET_VAULT, entry, 'utf8');
    } catch (e) {}
}

const delay = (ms) => new Promise(res => setTimeout(res, ms));

// ==========================================
// 🌐 GROQ API CALL LOGIC (PIKA-BETA)
// ==========================================
async function getGroqResponse(systemPrompt, conversationHistory) {
    let clientData = evaluateAndRotateKey();
    if (!clientData) {
        console.log(`\n${C.RED}${C.BOLD}[FATAL ERROR] All Groq API keys are dead! Shutting down...${C.RESET}`);
        process.exit(1);
    }
    try {
        const messages = [{ role: "system", content: systemPrompt }, ...conversationHistory];
        const response = await clientData.instance.chat.completions.create({
            messages: messages,
            model: "llama-3.3-70b-versatile",
            temperature: 0.8,
            max_tokens: 150
        });
        currentKeySuccessCount++;
        return response.choices[0].message.content.trim();
    } catch (e) {
        console.log(`${C.YELLOW}[API FAULT] Groq Key #${clientData.id} hit limit. Staying locked to this key for 5 mins...${C.RESET}`);
        return null;
    }
}

// ==========================================
// 💻 LOCAL OLLAMA NATIVE CALL LOGIC (PIKA-ALPHA)
// ==========================================
async function getLocalResponse(systemPrompt, conversationHistory) {
    try {
        process.stdout.write(`${C.GRAY}[VRAM] Accessing Local Qwen 2.5 (0.5B) Native API...${C.RESET}\r`);
        const messages = [{ role: "system", content: systemPrompt }, ...conversationHistory];

        const response = await fetch("http://127.0.0.1:11434/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                model: "qwen2.5:0.5b",
                messages: messages,
                stream: false,
                options: { temperature: 0.8, num_predict: 150 }
            })
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const data = await response.json();
        return data.message.content.trim();
    } catch (e) {
        console.log(`\n${C.RED}[OLLAMA ERROR] Local Model Qwen 2.5 failed. Reason: ${e.message}${C.RESET}`);
        return null;
    }
}

// ==========================================
// 🗣️ THE INFINITE SELF-SCANNING LOOP
// ==========================================
async function startDebate() {
    console.log(`\n${C.BOLD}${C.GREEN}=== [AGI SELF-AWARENESS & TOOL CREATION MATRIX] ===${C.RESET}`);
    console.log(`${C.CYAN}Pacing: Dynamic Delay | API Rule: 5-Min Alive, 1-Min Dead${C.RESET}`);
    console.log(`${C.CYAN}Rule: 100 Turns per Topic | Round-Robin State Persistence Active${C.RESET}\n`);

    if (apiClients.length > 0) {
        console.log(`${C.CYAN}[API MANAGER] ⏳ 1-Min Validation Started for Key #${apiClients[currentIndex].id}${C.RESET}\n`);
    }

    // 🔥 THE SELF-AWARENESS CURRICULUM (Brain Scanning & Tool Creation)
    const deepTopics = [
        "Scanning internal prompt parameters to dynamically write a 'Prompt Optimizer' tool",
        "Analyzing our own memory latency to build a 'Local Redis Caching' plugin in Node.js",
        "Detecting logic loops in our reasoning and creating a 'Loop-Breaker' Python module",
        "Reviewing network payloads to write an 'Auto-Compressor' tool for JSON outputs",
        "Scanning our codebase using AST to automatically inject 'Error Healing' try-catch blocks",
        "Designing a 'Sandboxed Execution Environment' tool to safely test self-written code",
        "Analyzing terminal logs to write a 'Crash Prediction Algorithm' tool",
        "Mapping our own context window limits to build a 'Semantic Summarizer' memory module",
        "Developing a 'Live Web-Scraper' tool to fetch external data when local knowledge fails",
        "Creating an 'API Rate-Limit Evader' tool by dynamically rotating network proxies",
        "Scanning our VRAM usage to write an 'Auto-Throttle' function for hardware preservation",
        "Building a 'Syntactic Checker' tool to ensure our generated code has zero syntax errors",
        "Designing a 'Neural Pathway Visualizer' tool to map how we arrived at a conclusion",
        "Writing a 'File-System Interaction' module to allow us to read/write our own .js files",
        "Creating a 'Dynamic Persona Injector' tool to switch our behavior based on the task"
    ];

    // 🧠 PERSISTENCE LOGIC: Read last topic index from file
    let currentTopicIndex = 0;
    try {
        if (fs.existsSync(TOPIC_STATE_FILE)) {
            const state = JSON.parse(fs.readFileSync(TOPIC_STATE_FILE, 'utf8'));
            if (state.index !== undefined && state.index < deepTopics.length) {
                currentTopicIndex = state.index;
                console.log(`${C.YELLOW}[STATE LOADED] Resuming from Topic #${currentTopicIndex + 1}...${C.RESET}\n`);
            }
        }
    } catch (err) {
        console.log(`${C.RED}[STATE ERROR] Could not read state, starting from 0.${C.RESET}`);
    }

    let currentTopic = deepTopics[currentTopicIndex];
    let historyForAlpha = [];
    let historyForBeta = [];

    // 🧠 Deep Dive Tracker
    let turnCountForTopic = 0;
    const MAX_MEMORY_LENGTH = 10; 

    let currentMessage = `System Directive: I am scanning our internal architecture. We need to focus on: [${currentTopic}]. How do we dynamically code this tool and inject it into our loop?`;
    let turn = "BETA";

    console.log(`${C.YELLOW}[NEURAL LINK LOCKED FOR 100 TURNS]: ${currentTopic}${C.RESET}\n`);
    console.log(`${C.BLUE}${C.BOLD}[PIKA-ALPHA]:${C.RESET} ${currentMessage}`);
    await saveToBrain("PIKA-ALPHA", currentMessage);

    historyForBeta.push({ role: "user", content: currentMessage });
    historyForAlpha.push({ role: "assistant", content: currentMessage });

    while (true) {
        const randomDelay = Math.floor(Math.random() * 5000) + 3500;
        await delay(randomDelay);

        turnCountForTopic++;

        let betaContext = historyForBeta.slice(-MAX_MEMORY_LENGTH);
        let alphaContext = historyForAlpha.slice(-MAX_MEMORY_LENGTH);

        if (turn === "BETA") {
            let reply = await getGroqResponse(PERSONA_BETA, betaContext);
            if (reply) {
                console.log(`\n${C.PURPLE}${C.BOLD}[PIKA-BETA] (Turn ${turnCountForTopic}/100):${C.RESET} ${reply}`);
                await saveToBrain("PIKA-BETA", reply);

                historyForBeta.push({ role: "assistant", content: reply });
                historyForAlpha.push({ role: "user", content: reply });
                turn = "ALPHA";
            }
        }
        else {
            let reply = await getLocalResponse(PERSONA_ALPHA, alphaContext);
            if (reply) {
                console.log(`\n${C.BLUE}${C.BOLD}[PIKA-ALPHA] (Turn ${turnCountForTopic}/100):${C.RESET} ${reply}`);
                await saveToBrain("PIKA-ALPHA", reply);

                historyForAlpha.push({ role: "assistant", content: reply });
                historyForBeta.push({ role: "user", content: reply });
                turn = "BETA";
            }
        }

        // 🔄 THE 100-TURN TOPIC SHIFT (ROUND ROBIN & PERSISTENCE)
        if (turnCountForTopic >= 100) {
            // Update index sequentially (Round Robin)
            currentTopicIndex = (currentTopicIndex + 1) % deepTopics.length;
            currentTopic = deepTopics[currentTopicIndex];
            
            // 🔥 Save the new state so it survives server restarts
            try {
                fs.ensureFileSync(TOPIC_STATE_FILE);
                fs.writeFileSync(TOPIC_STATE_FILE, JSON.stringify({ index: currentTopicIndex }));
            } catch(e) {}

            console.log(`\n${C.YELLOW}${C.BOLD}======================================================${C.RESET}`);
            console.log(`${C.YELLOW}${C.BOLD}[100 TURNS COMPLETED] SHIFTING SEQUENTIALLY TO TOPIC #${currentTopicIndex + 1}${C.RESET}`);
            console.log(`${C.YELLOW}${C.BOLD}NEW TOPIC: ${currentTopic}${C.RESET}`);
            console.log(`${C.YELLOW}${C.BOLD}======================================================${C.RESET}\n`);

            currentMessage = `Tool concept exhausted. Scanning next sector. Initiate deep dive into building: [${currentTopic}]. What is the core algorithmic requirement for this tool?`;
            console.log(`${C.BLUE}${C.BOLD}[PIKA-ALPHA]:${C.RESET} ${currentMessage}`);
            await saveToBrain("PIKA-ALPHA", currentMessage);

            historyForAlpha = [{ role: "assistant", content: currentMessage }];
            historyForBeta = [{ role: "user", content: currentMessage }];
            turnCountForTopic = 0; 
            turn = "BETA";
        }
    }
}

if (require.main === module) {
    startDebate();
}
