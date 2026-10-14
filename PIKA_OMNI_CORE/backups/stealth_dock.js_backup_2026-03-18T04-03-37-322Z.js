const fs = require('fs-extra');
const path = require('path');
const axios = require('axios');
const cheerio = require('cheerio'); // New Scraper Engine
const { trackAction } = require('./tracker.js');
const Groq = require('groq-sdk');
const { OpenAI } = require('openai'); // SambaNova Neural Interface
require('dotenv').config();

// ==========================================
// THE V10 DUAL-ROTATOR ENGINE
// ==========================================
const sambaKeys = process.env.SAMBANOVA_API_KEYS ? process.env.SAMBANOVA_API_KEYS.split(',') : [];
const sambaClients = sambaKeys.map(key => new OpenAI({
    apiKey: key.trim(),
    baseURL: "https://api.sambanova.ai/v1", // Direct SambaNova Server
}));

function getSamba() {
    if (sambaClients.length === 0) throw new Error("CRITICAL: SAMBANOVA_API_KEYS not found in .env!");
    const randomIndex = Math.floor(Math.random() * sambaClients.length);
    return sambaClients[randomIndex];
}

// Keeping Groq Engine initialized for potential hybrid use
const groqKeys = process.env.GROQ_API_KEYS ? process.env.GROQ_API_KEYS.split(',') : [];
const groqClients = groqKeys.map(key => new Groq({ apiKey: key.trim() }));

function getGroq() {
    if (groqClients.length === 0) throw new Error("CRITICAL: GROQ_API_KEYS not found in .env!");
    const randomIndex = Math.floor(Math.random() * groqClients.length);
    return groqClients[randomIndex];
}

const CACHE_FILE = path.join(__dirname, '../data/web_cache.json');

// TERMINAL COLORS
const C = { RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m", YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", RESET: "\x1b[0m" };

// ==========================================
// SYSTEM: WEB CACHE (Local Memory)
// ==========================================
async function getCache(query) {
    try {
        if (!fs.existsSync(CACHE_FILE)) return null;
        let cache = await fs.readJson(CACHE_FILE);
        let cleanQuery = query.toLowerCase().trim();
        // Return cache if queried within the last 24 hours
        if (cache[cleanQuery] && (Date.now() - cache[cleanQuery].timestamp < 86400000)) {
            return cache[cleanQuery].data;
        }
        return null;
    } catch (e) { 
        console.error(`${C.RED}[CACHE ERROR]${C.RESET}`, e.message); 
        return null; 
    }
}

async function saveCache(query, data) {
    try {
        await fs.ensureDir(path.join(__dirname, '../data'));
        let cache = fs.existsSync(CACHE_FILE) ? await fs.readJson(CACHE_FILE) : {};
        let cleanQuery = query.toLowerCase().trim();
        cache[cleanQuery] = { data: data, timestamp: Date.now() };
        await fs.writeJson(CACHE_FILE, cache, { spaces: 2 });
    } catch (e) { 
        console.error(`${C.RED}[CACHE ERROR]${C.RESET}`, e.message); 
    }
}

// ==========================================
// THE STEALTH DOCK ENGINE (Level 7)
// ==========================================
async function runStealthDock(query) {
    console.log(`\n${C.PURPLE}=== [STEALTH DOCK RUNNING] ===${C.RESET}`);
    let cleanQuery = query.toLowerCase().trim();

    // 1. CHECK CACHE (Zero API Cost)
    let cachedData = await getCache(cleanQuery);
    if (cachedData) {
        console.log(`${C.GREEN}[CACHE HIT]${C.RESET} Knowledge already exists in memory. (0 API Cost)`);
        trackAction("STEALTH_DOCK", "Cache_Hit", `Query: ${cleanQuery}`);
        return `[Source: Pika Web Cache]\n${cachedData}`;
    }

    trackAction("STEALTH_DOCK_STARTED", "Web_Hunt", `Target: ${cleanQuery}`);

    try {
        // SMART ROUTING (Weather & Crypto Hack)
        if (cleanQuery.includes('weather') || cleanQuery.includes('mausam')) {
            console.log(`${C.CYAN}[SMART ROUTE]${C.RESET} Fetching Live Weather from wttr.in...`);
            let city = cleanQuery.replace(/(what is the weather in|weather|mausam|in|ka|kya|hai)/g, '').trim() || 'Unchahar';
            const weatherRes = await axios.get(`https://wttr.in/${city}?format=3`, { timeout: 5000 });
            let wData = weatherRes.data.trim();
            await saveCache(cleanQuery, wData);
            return `[Live Weather API]\n${wData}`;
        }

        if (cleanQuery.includes('price of bitcoin') || cleanQuery.includes('btc price')) {
            console.log(`${C.CYAN}[SMART ROUTE]${C.RESET} Fetching Crypto from Binance...`);
            const btcRes = await axios.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', { timeout: 5000 });
            let pData = `Bitcoin (BTC) current price is $${parseFloat(btcRes.data.price).toFixed(2)}`;
            await saveCache(cleanQuery, pData);
            return `[Live Binance API]\n${pData}`;
        }

        // DUCK-DUCK-GO HTML SCRAPER (Strictly English)
        console.log(`${C.YELLOW}[DEEP WEB]${C.RESET} Bypassing Google. Scraping DuckDuckGo HTML in English...`);
        // Force English language search
        const ddgUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(cleanQuery)}&kl=us-en`;
        const headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9' // Force browser headers to English
        };
        const ddgResponse = await axios.get(ddgUrl, { headers, timeout: 8000 });
        const $ = cheerio.load(ddgResponse.data);

        let targetUrl = '';
        let searchSnippet = '';
        
        // Extract Top Result Link and Snippet
        $('.result').each((i, el) => {
            if (i === 0) {
                targetUrl = $(el).find('.result__url').attr('href');
                searchSnippet = $(el).find('.result__snippet').text().trim();
            }
        });

        if (targetUrl) {
            targetUrl = decodeURIComponent(targetUrl.replace('//duckduckgo.com/l/?uddg=', '').split('&')[0]);
            console.log(`${C.GREEN}[LINK FOUND]${C.RESET} Target locked: ${targetUrl.substring(0, 50)}...`);

            // DEEP ARTICLE X-RAY (Reading the actual page)
            try {
                console.log(`${C.CYAN}[X-RAY]${C.RESET} Extracting core text, removing ads and junk data...`);
                const pageRes = await axios.get(targetUrl, { headers, timeout: 8000 });
                const page$ = cheerio.load(pageRes.data);
                
                let articleText = '';
                page$('p').each((i, el) => {
                    let text = page$(el).text().trim();
                    if (text.length > 50) articleText += text + ' ';
                });

                articleText = articleText.substring(0, 2500);
                
                if (articleText.length > 200) {
                    console.log(`${C.PURPLE}[SAMBANOVA NEURAL]${C.RESET} Summarizing X-Ray data into Professional English...`);
                    // SHIFTED TO SAMBANOVA TO SAVE GROQ LIMITS
                    const summary = await getSamba().chat.completions.create({
                        messages: [
                            { role: "system", content: "You are the cognitive data extraction unit for Pika AGI. Summarize the following raw scraped text into 2-3 precise lines. CRITICAL INSTRUCTION: You MUST output the summary in PURE, PROFESSIONAL ENGLISH, regardless of the input language." },
                            { role: "user", content: `Query: ${cleanQuery}\n\nScraped Data:\n${articleText}` }
                        ],
                        model: "Meta-Llama-3-8B-Instruct", // SambaNova Model
                        temperature: 0.3,
                        max_tokens: 250
                    });

                    let finalAnswer = summary.choices[0].message.content;
                    await saveCache(cleanQuery, finalAnswer);
                    return `[Source: Deep Web Extract - ${new URL(targetUrl).hostname}]\n${finalAnswer}`;
                }
            } catch (xrayErr) {
                console.log(`${C.YELLOW}[X-RAY FAILED]${C.RESET} Page blocked scraping. Using DDG Snippet instead.`);
            }

            if (searchSnippet) {
                await saveCache(cleanQuery, searchSnippet);
                return `[Source: DuckDuckGo Snippet]\n${searchSnippet}`;
            }
        }

        // FALLBACK: SAMBANOVA LLM (Zero Search Match)
        console.log(`${C.YELLOW}[FALLBACK]${C.RESET} Web search empty. Querying internal neural memory...`);
        // SHIFTED TO SAMBANOVA
        const fallback = await getSamba().chat.completions.create({
            messages: [
                { role: "system", content: "You are Pika AGI. Provide a direct, precise answer to the user's query. No yapping. YOU MUST REPLY IN PURE ENGLISH, even if the user asks in Hindi/Hinglish." },
                { role: "user", content: query }
            ],
            model: "Meta-Llama-3-8B-Instruct", // SambaNova Model
            temperature: 0.4,
            max_tokens: 250
        });

        let fbAnswer = fallback.choices[0].message.content;
        await saveCache(cleanQuery, fbAnswer);
        return `[Source: Pika Neural Core]\n${fbAnswer}`;

    } catch (error) {
        trackAction("STEALTH_DOCK_ERROR", "Core_Crash", error.message);
        console.log(`\x1b[31m[DOCK CRITICAL ERROR]\x1b[0m ${error.message}`);
        return "System Warning: Internal network circuits are experiencing connection issues.";
    }
}

// Added error handling for potential API key issues
process.on('unhandledRejection', (reason, promise) => {
    console.error(`\x1b[31m[UNHANDLED REJECTION]\x1b[0m ${reason.message}`);
});

module.exports = { runStealthDock };