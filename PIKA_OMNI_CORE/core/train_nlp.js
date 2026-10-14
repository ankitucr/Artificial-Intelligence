const natural = require('natural');
const fs = require('fs-extra');
const path = require('path');
const { trackAction } = require('../services/tracker.js');
const { executeNeuralTask } = require('../core/router.js'); // 🛡️ Synced with Global Master Queue
require('dotenv').config();

// 📂 DYNAMIC ARCHITECTURAL PATHS
const DATA_DIR = path.join(__dirname, '../data');
const BACKUP_DIR = path.join(__dirname, '../backups');
const DATA_FILE = path.join(DATA_DIR, 'training_data.json');
const CONFIG_PATH = path.join(DATA_DIR, 'semantic_config.json');
const DATASET_VAULT = path.join(DATA_DIR, 'dataset_vault.jsonl'); // 🌟 The Foundation of your Offline LLM

// 🧠 ENSEMBLE BRAIN MATRICES
const BAYES_MODEL = path.join(DATA_DIR, 'pika_brain_bayes.json');
const LOGISTIC_MODEL = path.join(DATA_DIR, 'pika_brain_logistic.json');

// 🎨 PROFESSIONAL MATRIX COLORS
const C = { 
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m", 
    YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", BLUE: "\x1b[34m",
    RESET: "\x1b[0m", BOLD: "\x1b[1m" 
};

fs.ensureDirSync(DATA_DIR);
fs.ensureDirSync(BACKUP_DIR);

// ==========================================
// 🧬 POWER 1: SYNAPTIC WEIGHT INJECTION
// ==========================================
function applySynapticHack(text, config) {
    if (!text) return "";
    let words = text.toLowerCase().split(/\s+/);
    let augmentedText = text;

    words.forEach(word => {
        // High resonance tech core words
        if (config.tech_core?.[word] && config.tech_core[word].confidence >= 0.5) {
            augmentedText += ` ${word} ${word} ${word}`;
        }
        // High confidence action verbs
        else if (config.action?.[word] && config.action[word].confidence >= 0.5) {
            augmentedText += ` ${word} ${word}`;
        }
    });
    return augmentedText;
}

// ==========================================
// 🚀 POWER 2: SYNTHETIC DATA GENERATOR (API-Free via Router)
// ==========================================
async function generateSyntheticVariations(text) {
    console.log(`${C.PURPLE}[NEURAL SYNTHESIS]${C.RESET} Generating semantic clones for: "${text}"...`);
    
    const prompt = `You are a linguistic augmentation module for an AGI.
Analyze this sentence: "${text}"
Generate EXACTLY 4 distinct, highly accurate semantic variations (Hinglish/English mix allowed) meaning the same thing.
Output ONLY a strict JSON array of strings. No extra text.
Example: ["variation 1", "variation 2", "variation 3", "variation 4"]`;

    try {
        // 🛡️ Queued through Router to prevent API Rate Limits
        let rawJson = await executeNeuralTask(async () => {
            const { OpenAI } = require('openai');
            // Dynamically picking the first available SambaNova key for fast synthetic generation
            const sambaKey = process.env.SAMBA_1 || process.env.SAMBA_2 || process.env.SAMBA_3;
            if (!sambaKey) throw new Error("SambaNova Keys missing in .env");
            
            const sambaClient = new OpenAI({ apiKey: sambaKey.trim(), baseURL: "https://api.sambanova.ai/v1" });
            const response = await sambaClient.chat.completions.create({
                messages: [{ role: "system", content: prompt }],
                model: "Meta-Llama-3.1-70B-Instruct", // Upgraded to 70B for smarter Hinglish cloning
                temperature: 0.7, max_tokens: 300
            });
            return response.choices[0].message.content.trim();
        }, "Synthetic_Variations");

        const arrayMatch = rawJson.match(/\[[\s\S]*\]/);
        if (arrayMatch) {
            const variations = JSON.parse(arrayMatch[0]);
            if (Array.isArray(variations)) {
                console.log(`${C.GREEN}[SYNTHESIS SUCCESS]${C.RESET} ${variations.length} new neural pathways forged.`);
                return variations;
            }
        }
        throw new Error("Invalid array structure.");
    } catch (error) {
        console.error(`${C.YELLOW}[SYNTHESIS WARNING]${C.RESET} Augmentation bypassed: ${error.message}`);
        return [];
    }
}

// ==========================================
// 🧠 MAIN ENSEMBLE TRAINING ENGINE (Offline LLM Base)
// ==========================================
async function trainOmniBrain() {
    console.log(`\n${C.PURPLE}${C.BOLD}=== [AGI ML ENGINE] INITIATING SINGULARITY TRAINING ===${C.RESET}`);

    try {
        if (!fs.existsSync(DATA_FILE)) {
            const basicData = [
                { text: "hello how are you", intent: "GENERAL_CHAT" },
                { text: "kya haal hai", intent: "GENERAL_CHAT" },
                { text: "code likho", intent: "CORE_MUTATION" },
                { text: "banao isko", intent: "CORE_MUTATION" },
                { text: "fix this bug", intent: "SYSTEM_DIAGNOSTIC" },
                { text: "battery check karo", intent: "HARDWARE_SENSE" },
                { text: "search karo internet par", intent: "WEB_INTEL" }
            ];
            await fs.writeJson(DATA_FILE, basicData, { spaces: 2 });
            console.log(`${C.YELLOW}[SYSTEM]${C.RESET} Primary seeds (Hinglish+English) injected.`);
        }

        let trainingData = await fs.readJson(DATA_FILE);
        let config = await fs.readJson(CONFIG_PATH).catch(() => ({ tech_core: {}, action: {} }));

        // 🌟 THE TRUE VAULT INGESTION (Your Offline LLM Foundation)
        if (fs.existsSync(DATASET_VAULT)) {
            console.log(`${C.CYAN}[VAULT MERGE]${C.RESET} Mining Deep Archive for Offline AI Training...`);
            const vaultData = fs.readFileSync(DATASET_VAULT, 'utf8');
            const lines = vaultData.split('\n').filter(line => line.trim() !== '');
            let newRecords = 0;

            lines.forEach(line => {
                try {
                    const record = JSON.parse(line);
                    // Extract text smartly whether it's from Feeder, Mutator, or Tracker
                    let textExtract = record.prompt || record.concept || record.raw_input;
                    let intentExtract = record.intent || (record.type === "ARCHIVED_COGNITION" ? "KNOWLEDGE_EXTRACTION" : "GENERAL_CHAT");

                    if (textExtract && typeof textExtract === 'string' && textExtract.length < 200) {
                        const exists = trainingData.some(item => item.text === textExtract.toLowerCase() && item.intent === intentExtract);
                        if (!exists) {
                            trainingData.push({ text: textExtract.toLowerCase(), intent: intentExtract });
                            newRecords++;
                        }
                    }
                } catch (e) {} // Silently ignore malformed lines
            });

            if (newRecords > 0) {
                console.log(`${C.GREEN}[EXPANSION]${C.RESET} Merged ${newRecords} real-world experiences from Vault into Neural DB!`);
            }
        }

        // 2. Initialize Dual Classifiers
        const bayesClassifier = new natural.BayesClassifier();
        const logisticClassifier = new natural.LogisticRegressionClassifier();

        console.log(`${C.YELLOW}[DATA INGESTION]${C.RESET} Injecting ${trainingData.length} vectors into Omni-Brain...`);

        // 3. Mathematical Weighting
        trainingData.forEach(item => {
            if (!item.text || !item.intent) return;
            let boostedText = applySynapticHack(item.text, config);
            bayesClassifier.addDocument(boostedText, item.intent);
            logisticClassifier.addDocument(boostedText, item.intent);
        });

        // 4. Asynchronous Compilation (Prevents Termux Freezing)
        console.log(`${C.CYAN}[COMPILING]${C.RESET} Training Probabilistic (Bayes) & Pattern (Logistic) Networks...`);
        
        const startTime = Date.now();
        // Wrapping sync operations in a promise to allow event loop breathing room
        await new Promise(resolve => {
            bayesClassifier.train();
            logisticClassifier.train();
            resolve();
        });
        const trainTime = Date.now() - startTime;

        // 5. Securely Lock and Save Models
        bayesClassifier.save(BAYES_MODEL, () => {});
        logisticClassifier.save(LOGISTIC_MODEL, () => {});

        console.log(`${C.GREEN}✔️ Omni-Brain Matrices Locked & Saved. (${trainTime}ms)${C.RESET}`);
        trackAction("MODEL_TRAINED", "Ensemble Brain", `Compiled ${trainingData.length} vectors in ${trainTime}ms.`);
        console.log(`\n${C.GREEN}${C.BOLD}[EVOLUTION SUCCESS]${C.RESET} Pika's Machine Learning Core is fully operational! 🚀\n`);

    } catch (error) {
        console.error(`${C.RED}[CORE CRASH]${C.RESET} ML Engine Failure:`, error.message);
        trackAction("CRASH", "train_nlp.js", error.message);
    }
}

// ==========================================
// 🔄 POWER 3: CONTINUOUS ACTIVE LEARNING
// ==========================================
async function addKnowledgeAndRetrain(newText, intent) {
    try {
        console.log(`\n${C.CYAN}[ACTIVE LEARNING]${C.RESET} Assimilating: "${newText}" -> [${intent}]`);
        let trainingData = await fs.readJson(DATA_FILE).catch(() => []);

        const exists = trainingData.some(item => item.text.toLowerCase() === newText.toLowerCase() && item.intent === intent);
        if (!exists) {
            trainingData.push({ text: newText.toLowerCase(), intent: intent });
            let newAdditions = 1;

            // Singularity Expansion: Auto-generate clones
            const variations = await generateSyntheticVariations(newText);
            variations.forEach(varText => {
                const varExists = trainingData.some(item => item.text === varText.toLowerCase());
                if (!varExists) {
                    trainingData.push({ text: varText.toLowerCase(), intent: intent });
                    newAdditions++;
                }
            });

            await fs.writeJson(DATA_FILE, trainingData, { spaces: 2 });
            console.log(`${C.YELLOW}[DATASET EXPANDED]${C.RESET} Injected ${newAdditions} synaptic clones.`);
            trackAction("KNOWLEDGE_LEARNED", "training_data.json", `Added ${newAdditions} variations of intent: ${intent}`);

            // Recompile the brain dynamically
            await trainOmniBrain();
        } else {
            console.log(`${C.BLUE}[MEMORY HIT]${C.RESET} Knowledge already exists in matrix.`);
        }
    } catch (err) {
        console.error(`${C.RED}[LEARNING ERROR]${C.RESET}`, err.message);
    }
}

if (require.main === module) { trainOmniBrain(); }
module.exports = { trainOmniBrain, addKnowledgeAndRetrain };
