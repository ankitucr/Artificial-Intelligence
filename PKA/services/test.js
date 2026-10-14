// =====================================================================
// 🛠️ PKA TEST.JS : PRE-FLIGHT DIAGNOSIS ENGINE [FINAL GOD-MODE]
// Comprehensive System Check | API-Free Audit | Deep Web Ping Test
// =====================================================================

const fs = require('fs');
const path = require('path');
const market = require('./market_stream');
const { search } = require("duck-duck-scrape"); // 🕸️ DuckDuckGo Network Test

// 🎨 COLORS FOR HACKER TERMINAL UI
const cyan = "\x1b[36m";
const green = "\x1b[32m";
const yellow = "\x1b[33m";
const red = "\x1b[31m";
const reset = "\x1b[0m";

async function runSystemDiagnosis() {
    process.stdout.write("\x1Bc"); // Clear Screen
    console.log(`${cyan}==========================================================${reset}`);
    console.log(`${cyan}  🚀 P.K.A. NEURAL CORE : PRE-FLIGHT DIAGNOSIS ENGINE     ${reset}`);
    console.log(`${cyan}==========================================================${reset}`);

    // 📂 1. SYSTEM INTEGRITY CHECK (Files & Folders)
    console.log(`\n${yellow}[1/4] CHECKING SYSTEM INTEGRITY (DNA & Memory)...${reset}`);
    const coreFiles = ['runtime/state.json', 'data/memory.json', 'package.json', 'skills_vault'];
    
    coreFiles.forEach(file => {
        const fullPath = path.join(__dirname, file.startsWith('../') ? file : `../${file}`);
        // Simplified check assuming test.js might be in a core folder or root
        const checkPath = fs.existsSync(path.join(__dirname, file)) ? path.join(__dirname, file) : path.join(__dirname, '..', file);
        
        const status = fs.existsSync(checkPath) ? `${green}OK${reset}` : `${red}MISSING${reset}`;
        console.log(`   - ${file.padEnd(25)} : [${status}]`);
    });

    // 👁️ 2. OMNISCIENT RADAR CHECK (TradingView + Sentiments)
    console.log(`\n${yellow}[2/4] TESTING OMNISCIENT RADAR (TradingView Signals)...${reset}`);
    try {
        console.log(`   - Initiating API-Free Global Pulse Scan...`);
        const pulse = await market.getGlobalMarketPulse();

        if (pulse && pulse.data) {
            const btcStatus = pulse.data.crypto["BTCUSDT"] ? pulse.data.crypto["BTCUSDT"].recommendation : "N/A";
            console.log(`   - ${green}BTC/USDT Signal${reset}  : ${btcStatus}`);
            console.log(`   - ${green}Market Sentiment${reset} : ${pulse.sentiment}`);
            console.log(`   - Status           : [${green}SUCCESSFUL${reset}]`);
        } else {
            throw new Error("Empty Data Stream");
        }
    } catch (e) {
        console.log(`   - Status           : [${red}FAILED: ${e.message}${reset}]`);
    }

    // 🕸️ 3. DEEP WEB CONNECTION AUDIT (DuckDuckGo Ping)
    console.log(`\n${yellow}[3/4] TESTING DEEP WEB CONNECTION (DuckDuckGo)...${reset}`);
    try {
        console.log(`   - Pinging Open Web Scraper...`);
        const searchResults = await search("PKA AGI systemic connection test", { safeSearch: "moderate" });
        
        if (searchResults.results && searchResults.results.length > 0) {
            console.log(`   - ${green}Web Access${reset}       : ONLINE`);
            console.log(`   - ${green}Network Nodes${reset}    : Connected (${searchResults.results.length} routes found)`);
            console.log(`   - Status           : [${green}SUCCESSFUL${reset}]`);
        } else {
            throw new Error("No web data returned.");
        }
    } catch (e) {
        console.log(`   - Status           : [${red}FAILED: Network Blocked or Offline${reset}]`);
    }

    // 🧠 4. NEURAL LINK AUDIT (Intelligence State)
    console.log(`\n${yellow}[4/4] AUDITING NEURAL INTELLIGENCE STATE...${reset}`);
    try {
        const statePath = fs.existsSync(path.join(__dirname, 'runtime/state.json')) ? path.join(__dirname, 'runtime/state.json') : path.join(__dirname, '..', 'runtime/state.json');
        const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
        
        console.log(`   - IQ Level         : ${(state.intelligence || 0).toFixed(2)}`);
        console.log(`   - Vocabulary Size  : ${state.vocabulary ? state.vocabulary.length : 0} Words`);
        console.log(`   - Mastery Level    : Trading [${(state.mastery?.trading_logic || state.mastery?.self_evolution || 0).toFixed(4)}]`);
        console.log(`   - Status           : [${green}HYPER-STABLE${reset}]`);
    } catch (e) {
        console.log(`   - Status           : [${red}CORRUPT OR MISSING (Run recover.js)${reset}]`);
    }

    console.log(`\n${cyan}==========================================================${reset}`);
    console.log(`   ${green}DIAGNOSIS COMPLETE. SYSTEM READY FOR GOD-MODE.${reset}`);
    console.log(`${cyan}==========================================================${reset}\n`);
}

// 🚀 RUN DIAGNOSIS
runSystemDiagnosis();
