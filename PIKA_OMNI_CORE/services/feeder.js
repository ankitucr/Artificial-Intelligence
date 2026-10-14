const fs = require('fs-extra');
const path = require('path');
const { readMemory, saveMemory } = require('../core/memory_manager.js');
const { trackAction } = require('./tracker.js');

// 🧠 Master Brain Sync
const { executeNeuralTask } = require('../core/router.js');       
require('dotenv').config();

// 📂 DYNAMIC PATHS
const MASS_TRAIN_FILE = path.join(__dirname, '../data/mass_train.txt');
const DATASET_VAULT = path.join(__dirname, '../data/dataset_vault.jsonl');

// 🎨 PROFESSIONAL MATRIX COLORS
const C = { 
    CYAN: "\x1b[38;5;51m", 
    PURPLE: "\x1b[38;5;213m", 
    GREEN: "\x1b[38;5;82m", 
    RED: "\x1b[38;5;196m", 
    YELLOW: "\x1b[38;5;226m", 
    BLUE: "\x1b[38;5;45m",
    RESET: "\x1b[0m",
    BOLD: "\x1b[1m"
};

// ==========================================
// 🧠 VAULT INJECTION (The Offline AGI Dream)
// ==========================================
async function vaultKnowledge(type, raw, analysis) {
    try {
        const entry = JSON.stringify({
            timestamp: new Date().toISOString(),
            ingestion_type: type,
            raw_input: raw.substring(0, 3000),
            structured_logic: analysis
        }) + '\n';
        await fs.appendFile(DATASET_VAULT, entry, 'utf8');
        console.log(`${C.GREEN}[VAULTED]${C.RESET} Intelligence segment archived for future training.`);
    } catch (e) {
        console.error(`${C.RED}[VAULT ERROR]${C.RESET} Failed to archive intelligence.`);
    }
}

// ==========================================
// 🧠 NEURAL SEMANTIC POST-MORTEM (API-Free)
// ==========================================
async function deepPostMortemLLM(code, lang) {
    console.log(`${C.PURPLE}[NEURAL CORE]${C.RESET} Synthesizing ${C.BLUE}${lang}${C.RESET} logic structures...`);                       

    const prompt = `You are Pika AGI, an expert Knowledge Extractor. Analyze the provided text/code and respond ONLY in valid JSON.
Format:
{
  "title": "Short unique ID",
  "summary": "2-sentence explanation",
  "tags": ["#tag1", "#tag2"],
  "learning_concepts": ["concept1", "concept2"],
  "anatomy": { "functions": [], "classes": [], "dependencies": [] },
  "use_case": "Real world application"
}
INPUT:
\`\`\`${lang}
${code}
\`\`\`
`;

    try {
        // 🌟 Synced with Router's Global Queue. No standalone keys used here.
        let jsonStr = await executeNeuralTask(async () => {       
            const { Groq } = require('groq-sdk');
            const groq = new Groq({ apiKey: process.env.GROQ_1 || process.env.GROQ_2 });
            const response = await groq.chat.completions.create({
                messages: [{ role: "system", content: prompt }],
                model: "llama-3.3-70b-versatile",             
                temperature: 0.1
            });                                               
            return response.choices[0].message.content.trim();
        }, `Feeder_Analyze_${lang}`);

        const jsonMatch = jsonStr.match(/\{[\s\S]*\}/);           
        if (!jsonMatch) throw new Error("Neural response contained no JSON.");
        
        return JSON.parse(jsonMatch[0]);
    } catch (err) {
        console.error(`${C.RED}[NEURAL FAIL]${C.RESET} Fallback engaged: ${err.message}`);
        return { title: "Raw_Logic_" + Date.now(), summary: "Raw data extraction.", tags: ["#raw"], learning_concepts: [], anatomy: {}, use_case: "Manual review required" };
    }
}                                                                 

// ==========================================
// 🌟 ENVIRONMENTAL SENSORY EVOLUTION
// ==========================================
async function ingestSensoryMemory(pendingArray) {
    try {
        let sensoryDataList = await readMemory('sensory_memory.json') || [];
        if (sensoryDataList.length === 0) return pendingArray;

        console.log(`${C.CYAN}[SENSORS]${C.RESET} Ingesting physical world patterns into neural pathways...`);
        let latestSense = sensoryDataList[sensoryDataList.length - 1]; 

        // 🌡️ Hardware Intelligence
        if (latestSense.powerVitals?.battery?.status === 'SUCCESS') {
            let bat = latestSense.powerVitals.battery.data.percentage;
            if (bat < 20) {
                pendingArray.push(`Low-Power Survival: Systems at ${bat}%`);
                console.log(`${C.YELLOW}[SENSE]${C.RESET} Survival instinct triggered (Low Battery).`);
            }
        }

        // 📶 Connection Intelligence
        if (latestSense.networkVitals?.wifi?.status === 'SUCCESS') {
            pendingArray.push("Network Topology: Active Ingestion");
        }

        // Wipe processed sensory data to keep memory clean
        await saveMemory('sensory_memory.json', []);
        return pendingArray;
    } catch (err) { return pendingArray; }
}

// ==========================================
// 🚀 THE MAIN FEEDER ENGINE
// ==========================================
async function startFeeder() {
    try {
        if (!fs.existsSync(MASS_TRAIN_FILE)) return;
        let rawText = await fs.readFile(MASS_TRAIN_FILE, 'utf8');
        if (rawText.trim().length === 0) return;

        console.log(`\n${C.CYAN}${C.BOLD}=== [DATA INGESTION SEQUENCE INITIATED] ===${C.RESET}`);
        console.log(`${C.YELLOW}[INGEST]${C.RESET} Processing new intelligence from mass_train.txt...`);                                                                                      
        
        let codeVault = await readMemory('code_vault.json') || {};
        let pending = await readMemory('pending_learning.json') || [];
        let lines = rawText.split('\n');
        let newLogicsLearned = 0;                                 

        const pushToPending = (items) => {
            if (Array.isArray(items)) {
                items.forEach(item => {                           
                    let clean = item.replace('#', '').trim();
                    if (clean.length > 2 && clean.length < 50 && !pending.includes(clean)) pending.push(clean);
                });
            }
        };

        async function processBlock(codeLines, language) {
            let fullText = codeLines.join('\n');
            if (fullText.trim().length > 10) {
                let analysis = await deepPostMortemLLM(fullText, language);
                let key = analysis.title.toLowerCase().replace(/[^a-z0-9]/g, '_');

                codeVault[key] = { ...analysis, source_code: fullText, timestamp: new Date().toISOString() };

                // 🌟 Dataset Vaulting for Offline AGI
                await vaultKnowledge(language, fullText, analysis);

                // Extract all child concepts for the Crawler
                if (analysis.anatomy) {                           
                    pushToPending(analysis.anatomy.functions);
                    pushToPending(analysis.anatomy.classes);
                    pushToPending(analysis.anatomy.dependencies); 
                }
                pushToPending(analysis.tags);                     
                pushToPending(analysis.learning_concepts);

                console.log(`${C.GREEN}[DIGESTED]${C.RESET} Integrated ${C.BOLD}${analysis.title}${C.RESET} into Code Vault.`);
                newLogicsLearned++;
            }
        }

        // ⚡ Intelligent Block Splitting
        if (!rawText.includes('```')) {
            await processBlock(lines, "text");
        } else {
            let isCodeMode = false, currentCode = [], codeLang = "text";
            for (let line of lines) {              
                let trimmed = line.trim();
                if (trimmed.startsWith('```')) {
                    if (!isCodeMode) { isCodeMode = true; codeLang = trimmed.replace('```', '').trim() || "javascript"; currentCode = []; }
                    else { isCodeMode = false; await processBlock(currentCode, codeLang); }
                    continue;
                }
                if (isCodeMode) currentCode.push(line);
            }
        }

        // 🚀 Evolutionary Sync
        pending = await ingestSensoryMemory(pending);
        await saveMemory('code_vault.json', codeVault);           
        await saveMemory('pending_learning.json', pending);

        // 🧹 Clean mass train file to prevent loops
        await fs.writeFile(MASS_TRAIN_FILE, '');
        console.log(`${C.CYAN}[SYNC]${C.RESET} Feeder cycle completed successfully.\n`);
        try { trackAction("FEEDER_SUCCESS", "mass_train.txt", `${newLogicsLearned} units processed.`); } catch(e){}

    } catch (error) {
        console.log(`${C.RED}[FEEDER CRASH]${C.RESET} Critical failure: ${error.message}`);                     
    }
}                                                                 

module.exports = { startFeeder };
