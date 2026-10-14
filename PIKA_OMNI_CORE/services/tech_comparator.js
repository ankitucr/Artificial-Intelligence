const fs = require('fs-extra');
const path = require('path');
const { trackAction } = require('./tracker.js');
const Groq = require('groq-sdk');
require('dotenv').config();

// 🌟 THE UPGRADE: Importing Global Queue from the Master Router
const { executeNeuralTask } = require('../core/router.js');

// 📂 DYNAMIC PATHS
const TECH_KNOWLEDGE_FILE = path.join(__dirname, '../data/tech_knowledge.json');
const DATASET_VAULT = path.join(__dirname, '../data/dataset_vault.jsonl'); // 🌟 Local LLM Dream

// 🎨 PROFESSIONAL TERMINAL COLORS
const C = { 
    RED: "\x1b[31m", 
    GREEN: "\x1b[32m", 
    CYAN: "\x1b[36m", 
    YELLOW: "\x1b[33m", 
    PURPLE: "\x1b[35m", 
    BLUE: "\x1b[34m",
    RESET: "\x1b[0m",
    BOLD: "\x1b[1m"
};

// ==========================================
// 🧠 VAULT LOGGING (Self-Dependent Learning)
// ==========================================
async function logToVault(topic, data) {
    try {
        const entry = JSON.stringify({
            timestamp: new Date().toISOString(),
            type: "TECH_COMPARISON_LEARNED",
            topic: topic,
            knowledge: data
        }) + '\n';
        await fs.appendFile(DATASET_VAULT, entry, 'utf8');
    } catch (e) {
        // Silently ignore to keep UI clean
    }
}

// ==========================================
// 🧠 LOCAL MEMORY MANAGEMENT
// ==========================================
async function loadTechKnowledge() {
    try {
        if (!fs.existsSync(TECH_KNOWLEDGE_FILE)) {
            const emptyBrain = { comparisons: {} };
            await fs.writeJson(TECH_KNOWLEDGE_FILE, emptyBrain, { spaces: 2 });
            return emptyBrain;
        }
        return await fs.readJson(TECH_KNOWLEDGE_FILE);
    } catch (err) {
        console.error(`${C.RED}[TECH KNOWLEDGE ERROR]${C.RESET} Failed to load local database:`, err.message);
        return { comparisons: {} };
    }
}

async function saveTechKnowledge(data) {
    try {
        await fs.writeJson(TECH_KNOWLEDGE_FILE, data, { spaces: 2 });
    } catch (err) {
        console.error(`${C.RED}[TECH SAVE ERROR]${C.RESET} Failed to write to disk:`, err.message);
    }
}

// ==========================================
// ⚙️ THE COMPARATOR ENGINE (API-Free & Bulletproof)
// ==========================================
async function generateComparisonWithLLM(query) {
    console.log(`${C.PURPLE}[AI ARCHITECT]${C.RESET} Pika is dynamically analyzing: ${C.YELLOW}${query}${C.RESET}`);

    const systemPrompt = `You are Pika, an expert software architect. The user is requesting a technical comparison of two or more technologies, or detailed specifications of a tech stack.
Your response MUST be EXACTLY in the following JSON format, without any conversational text or markdown formatting.
{
  "title": "⚙️ [Comparison Title]",
  "description": "[1-2 line simple description of what this comparison entails]",
  "options": [
    {
      "name": "[Tech Name 1]",
      "pros": "[2-3 strong advantages]",
      "cons": "[2-3 strong disadvantages]"
    },
    {
      "name": "[Tech Name 2]",
      "pros": "[2-3 strong advantages]",
      "cons": "[2-3 strong disadvantages]"
    }
  ],
  "verdict": "💡 Pika's Advice: [Clear, highly technical but easy-to-understand final recommendation based on real-world use cases.]"
}`;

    try {
        // 🌟 THE UPGRADE: Synced with Router's Main Gate. No standalone API engine needed.
        let rawResponse = await executeNeuralTask(async () => {
            // Lightweight instant client just for this task (prevents memory leaks)
            const groq = new Groq({ apiKey: process.env.GROQ_1 || process.env.GROQ_2 });
            const chatCompletion = await groq.chat.completions.create({
                messages: [
                    { role: "system", content: systemPrompt },
                    { role: "user", content: `Compare or explain: ${query}` }
                ],
                model: "llama-3.3-70b-versatile",
                temperature: 0.2,
                max_tokens: 1500
            });
            return chatCompletion.choices[0].message.content.trim();
        }, `Tech_Compare_${query.substring(0, 10).replace(/\s/g, '_')}`);

        // 🌟 THE UPGRADE: Bulletproof JSON Extractor (Regex)
        // Even if LLM hallucinates and adds "Here is your JSON:" before the code, this will extract only the pure JSON.
        const jsonMatch = rawResponse.match(/\{[\s\S]*\}/);
        
        if (!jsonMatch) {
            throw new Error("No valid JSON structure found in Neural Response.");
        }

        return JSON.parse(jsonMatch[0]);

    } catch (err) {
        console.error(`${C.RED}[LLM GENERATION FAILED]${C.RESET} Failed to extract structured comparison.`, err.message);
        return null;
    }
}

// ==========================================
// 🚀 MAIN EXECUTION LOGIC
// ==========================================
async function compareTech(inputParams) {
    if (!inputParams) return null;
    if (Array.isArray(inputParams) && inputParams.length === 0) return null;

    let query = Array.isArray(inputParams) ? inputParams.join(' ') : inputParams;
    let cleanQuery = query.toLowerCase().trim();

    if (!cleanQuery) return null;

    let db = await loadTechKnowledge();

    // Check if Pika already knows this
    let existingMatch = Object.keys(db.comparisons).find(k => k.includes(cleanQuery) || cleanQuery.includes(k));

    let comparisonData = null;

    if (existingMatch) {
        console.log(`${C.CYAN}[TECH MEMORY HIT]${C.RESET} Comparison loaded instantly from Pika's Vault.`);
        comparisonData = db.comparisons[existingMatch];
        try { trackAction("TECH_COMPARISON", "Memory", `Retrieved: ${existingMatch}`); } catch(e){}
    } else {
        console.log(`${C.YELLOW}[NEW TECH DETECTED]${C.RESET} No local data found. Initiating Auto-Generation...`);
        comparisonData = await generateComparisonWithLLM(query);

        if (comparisonData) {
            // Save to quick memory
            db.comparisons[cleanQuery] = comparisonData;
            await saveTechKnowledge(db);
            
            // 🌟 Save to Deep Vault for future offline LLM training
            await logToVault(cleanQuery, comparisonData);

            try { trackAction("TECH_LEARNED", "LLM", `Auto-learned & saved: ${cleanQuery}`); } catch(e){}
            console.log(`${C.GREEN}${C.BOLD}[TECH LEARNED]${C.RESET} Pika has permanently memorized this technical comparison.`);
        }
    }

    if (!comparisonData) {
        return "System Warning: Neural core failed to analyze this technology comparison. Please check API limits or try again later.";
    }

    // Format the final output cleanly
    let reply = `\n${comparisonData.title}\n${comparisonData.description}\n\n`;

    if (comparisonData.options && Array.isArray(comparisonData.options)) {
        comparisonData.options.forEach(opt => {
            reply += `🔹 **${opt.name}**\n   ✅ Pros: ${opt.pros}\n   ❌ Cons: ${opt.cons}\n\n`;
        });
    }

    reply += `${comparisonData.verdict}\n`;
    return reply;
}

module.exports = { compareTech };
