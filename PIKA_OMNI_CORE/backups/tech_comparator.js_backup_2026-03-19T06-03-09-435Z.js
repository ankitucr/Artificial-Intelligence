const fs = require('fs-extra');
const path = require('path');
const { trackAction } = require('./tracker.js');
const Groq = require('groq-sdk');
const { OpenAI } = require('openai'); 
require('dotenv').config();

const groqKeys = process.env.GROQ_API_KEYS ? process.env.GROQ_API_KEYS.split(',') : [];
const groqClients = groqKeys.map(key => new Groq({ apiKey: key.trim() }));

function getGroq() {
    if (groqClients.length === 0) throw new Error("CRITICAL: GROQ_API_KEYS not found in .env!");
    const randomIndex = Math.floor(Math.random() * groqClients.length);
    return groqClients[randomIndex];
}

const sambaKeys = process.env.SAMBANOVA_API_KEYS ? process.env.SAMBANOVA_API_KEYS.split(',') : [];
const sambaClients = sambaKeys.map(key => new OpenAI({
    apiKey: key.trim(),
    baseURL: "https://api.sambanova.ai/v1",
}));

function getSamba() {
    if (sambaClients.length === 0) throw new Error("CRITICAL: SAMBANOVA_API_KEYS not found in .env!");
    const randomIndex = Math.floor(Math.random() * sambaClients.length);
    return sambaClients[randomIndex];
}

const TECH_KNOWLEDGE_FILE = path.join(__dirname, '../data/tech_knowledge.json');

const C = { RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m", YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", RESET: "\x1b[0m" };

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

async function generateComparisonWithLLM(query) {
    console.log(`${C.PURPLE}[AI ARCHITECT]${C.RESET} Pika is dynamically analyzing '${query}'...`);

    const systemPrompt = `You are Pika, an expert software architect. The user is requesting a technical comparison of two or more technologies, or detailed specifications of a tech stack.
Your response MUST be EXACTLY in the following JSON format, without any conversational text or markdown formatting (\`\`\`).
STRICT JSON FORMAT:
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
        const chatCompletion = await getGroq().chat.completions.create({
            messages: [
                { role: "system", content: systemPrompt },
                { role: "user", content: `Compare or explain: ${query}` }
            ],
            model: "llama-3.3-70b-versatile",
            temperature: 0.2, 
            max_tokens: 1000
        });

        let rawResponse = chatCompletion.choices[0].message.content.trim();

        if (rawResponse.startsWith('```json')) rawResponse = rawResponse.replace(/```json/g, '');
        if (rawResponse.startsWith('```')) rawResponse = rawResponse.replace(/```/g, '');
        rawResponse = rawResponse.trim();

        return JSON.parse(rawResponse);
    } catch (err) {
        console.error(`${C.RED}[LLM GENERATION FAILED]${C.RESET} Failed to generate JSON comparison.`, err.message);
        return null;
    }
}

async function compareTech(inputParams) {
    if (!inputParams) return null;
    if (Array.isArray(inputParams) && inputParams.length === 0) return null;

    let query = Array.isArray(inputParams) ? inputParams.join(' ') : inputParams;
    let cleanQuery = query.toLowerCase().trim();

    if (!cleanQuery) return null;

    let db = await loadTechKnowledge();

    let existingMatch = Object.keys(db.comparisons).find(k => k.includes(cleanQuery) || cleanQuery.includes(k));

    let comparisonData = null;

    if (existingMatch) {
        console.log(`${C.GREEN}[TECH MEMORY HIT]${C.RESET} Comparison loaded from Pika's Vault.`);
        comparisonData = db.comparisons[existingMatch];
        trackAction("TECH_COMPARISON", "Memory", `Retrieved: ${existingMatch}`);
    } else {
        console.log(`${C.YELLOW}[NEW TECH DETECTED]${C.RESET} No local data found. Initiating Auto-Generation...`);
        comparisonData = await generateComparisonWithLLM(query);

        if (comparisonData) {
            db.comparisons[cleanQuery] = comparisonData;
            await saveTechKnowledge(db);
            trackAction("TECH_LEARNED", "LLM", `Auto-learned & saved: ${cleanQuery}`);
            console.log(`${C.GREEN}[TECH LEARNED]${C.RESET} Pika has permanently memorized this technical comparison.`);
        }
    }

    if (!comparisonData) {
        return "System Warning: Internal error occurred while analyzing this technology comparison. Please try again later.";
    }

    let reply = `${comparisonData.title}\n${comparisonData.description}\n\n`;

    if (comparisonData.options && Array.isArray(comparisonData.options)) {
        comparisonData.options.forEach(opt => {
            reply += `🔹 **${opt.name}**\n   ✅ Pros: ${opt.pros}\n    ❌ Cons: ${opt.cons}\n\n`;
        });
    }

    reply += `${comparisonData.verdict}`;
    return reply;
}

try {
    module.exports = { compareTech };
} catch (err) {
    console.error(`${C.RED}[MODULE EXPORT ERROR]${C.RESET} Failed to export module:`, err.message);
}