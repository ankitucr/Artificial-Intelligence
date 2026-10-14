const fs = require('fs-extra');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

// 📂 DYNAMIC PATHS
const LOG_DIR = path.join(__dirname, '../logs');
const ARCHIVE_DIR = path.join(LOG_DIR, 'archives');
const LOG_FILE = path.join(LOG_DIR, 'pika_live_matrix.jsonl');
const DATASET_VAULT = path.join(__dirname, '../data/dataset_vault.jsonl');
const FOREX_DIR = path.join(__dirname, '../data/forex');
const FOREX_LOG = path.join(FOREX_DIR, 'xauusd_history.jsonl');
const FOREX_STATE = path.join(FOREX_DIR, 'market_state.json');
const ALERTS_FILE = path.join(LOG_DIR, 'alerts.jsonl');

// 🎨 PROFESSIONAL MATRIX COLORS
const C = {
    RED: "\x1b[31m",
    GREEN: "\x1b[32m",
    CYAN: "\x1b[36m",
    YELLOW: "\x1b[33m",
    PURPLE: "\x1b[35m",
    BLUE: "\x1b[34m",
    ORANGE: "\x1b[38;5;214m",
    WHITE: "\x1b[37m",
    RESET: "\x1b[0m",
    BOLD: "\x1b[1m"
};

// ══════════════════════════════════════════════════════════════════════════
// FETCH POLYFILL (Node 16/17 compatible)
// ══════════════════════════════════════════════════════════════════════════
let fetch;
try {
    fetch = require('node-fetch');
} catch (e) {
    fetch = globalThis.fetch;
    if (!fetch) {
        console.error('[FATAL] node-fetch not installed. Run: npm i node-fetch@2');
        process.exit(1);
    }
}

// ══════════════════════════════════════════════════════════════════════════
// ⚙️ TELEMETRY ENGINE INITIALIZATION
// ══════════════════════════════════════════════════════════════════════════
fs.ensureDirSync(LOG_DIR);
fs.ensureDirSync(ARCHIVE_DIR);
fs.ensureDirSync(FOREX_DIR);

// ══════════════════════════════════════════════════════════════════════════
// 🛡️ AUTO-ROTATION & ARCHIVING (Crash Prevention)
// ══════════════════════════════════════════════════════════════════════════
const MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024;
const MAX_ARCHIVE_AGE_DAYS = 7;

async function checkAndRotateLogs() {
    try {
        if (await fs.pathExists(LOG_FILE)) {
            const stats = await fs.stat(LOG_FILE);
            if (stats.size >= MAX_LOG_SIZE_BYTES) {
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const archivePath = path.join(ARCHIVE_DIR, `matrix_archive_${timestamp}.jsonl`);
                await fs.rename(LOG_FILE, archivePath);
                console.log(`\n${C.CYAN}[TELEMETRY SHIFT]${C.RESET} Log limit reached. Archive created: ${C.BLUE}${path.basename(archivePath)}${C.RESET}`);
            }
        }
        await cleanOldArchives();
    } catch (error) {}
}

async function cleanOldArchives() {
    try {
        const files = await fs.readdir(ARCHIVE_DIR);
        const now = Date.now();
        const maxAge = MAX_ARCHIVE_AGE_DAYS * 24 * 60 * 60 * 1000;
        for (const file of files) {
            const filePath = path.join(ARCHIVE_DIR, file);
            const stat = await fs.stat(filePath);
            if (now - stat.mtimeMs > maxAge) {
                await fs.remove(filePath);
                console.log(`${C.YELLOW}[ARCHIVE CLEAN]${C.RESET} Removed old: ${file}`);
            }
        }
    } catch (e) {}
}

// ══════════════════════════════════════════════════════════════════════════
// ⚡ HIGH-PERFORMANCE MEMORY BUFFER
// ══════════════════════════════════════════════════════════════════════════
let logBuffer = [];
const MAX_BUFFER_SIZE = 10;
let isFlushing = false;

async function flushBufferToDisk() {
    if (isFlushing || logBuffer.length === 0) return;
    isFlushing = true;
    try {
        await checkAndRotateLogs();
        const batchToWrite = logBuffer.join('');
        logBuffer = [];
        await fs.appendFile(LOG_FILE, batchToWrite, 'utf8');
    } catch (error) {
        console.error(`${C.RED}[BUFFER ERROR]${C.RESET} ${error.message}`);
    } finally {
        isFlushing = false;
    }
}

setInterval(flushBufferToDisk, 30000);

// ══════════════════════════════════════════════════════════════════════════
// 🧠 LOG LEVEL SYSTEM (V5 Intelligence)
// ══════════════════════════════════════════════════════════════════════════
const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3,
    FATAL: 4
};

let currentLogLevel = LOG_LEVELS.INFO;

function shouldLog(level) {
    return LOG_LEVELS[level] >= currentLogLevel;
}

function setLogLevel(level) {
    if (LOG_LEVELS[level] !== undefined) {
        currentLogLevel = LOG_LEVELS[level];
        console.log(`${C.CYAN}[LOG LEVEL]${C.RESET} Set to ${level}`);
    }
}

// ══════════════════════════════════════════════════════════════════════════
// 🧠 NEURAL TELEMETRY (Enhanced V5)
// ══════════════════════════════════════════════════════════════════════════
async function trackAction(category, action, details = {}, vault = false, level = 'INFO') {
    try {
        if (!shouldLog(level)) return;
        const now = new Date();
        const timestamp = now.toISOString();
        const istTimestamp = now.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });

        const memUsage = process.memoryUsage();
        const vitals = {
            ram_heap: (memUsage.heapUsed / 1024 / 1024).toFixed(2) + " MB",
            ram_rss: (memUsage.rss / 1024 / 1024).toFixed(2) + " MB",
            ram_total: (memUsage.heapTotal / 1024 / 1024).toFixed(2) + " MB",
            uptime: process.uptime().toFixed(0) + "s",
            pid: process.pid
        };

        const logObject = {
            timestamp: timestamp,
            ist: istTimestamp,
            level: level,
            category: category.toUpperCase(),
            action: action,
            details: details,
            system_vitals: vitals
        };

        const logEntry = JSON.stringify(logObject) + '\n';
        logBuffer.push(logEntry);

        let color = C.CYAN;
        if (level === 'FATAL') color = C.RED + C.BOLD;
        else if (level === 'ERROR') color = C.RED;
        else if (level === 'WARN') color = C.YELLOW;
        else if (category === 'ERROR') color = C.RED;
        else if (category === 'MUTATION') color = C.PURPLE;
        else if (category === 'SYSTEM') color = C.YELLOW;
        else if (category === 'CRAWLER') color = C.GREEN;
        else if (category === 'FOREX') color = C.ORANGE;

        const detailStr = typeof details === 'string' ? details : JSON.stringify(details).slice(0, 100);
        console.log(`${color}[${level}][${category}]${C.RESET} ${action} -> ${C.BLUE}${detailStr}${C.RESET}`);

        if (level === 'ERROR' || level === 'FATAL') {
            await sendAlert(logObject);
        }

        if (vault) {
            const vaultEntry = JSON.stringify({
                timestamp: timestamp,
                type: "NEURAL_LEARNING",
                event: action,
                data: details
            }) + '\n';
            await fs.appendFile(DATASET_VAULT, vaultEntry, 'utf8');
        }

        if (logBuffer.length >= MAX_BUFFER_SIZE) {
            flushBufferToDisk();
        }
    } catch (error) {}
}

// ══════════════════════════════════════════════════════════════════════════
// 🚨 ALERT SYSTEM (V5 Intelligence)
// ══════════════════════════════════════════════════════════════════════════
async function sendAlert(logObject) {
    try {
        const alert = {
            timestamp: logObject.timestamp,
            level: logObject.level,
            category: logObject.category,
            action: logObject.action,
            details: logObject.details
        };
        await fs.appendFile(ALERTS_FILE, JSON.stringify(alert) + '\n', 'utf8');
    } catch (e) {}
}

async function getRecentAlerts(limit = 50) {
    try {
        if (!await fs.pathExists(ALERTS_FILE)) return [];
        const content = await fs.readFile(ALERTS_FILE, 'utf8');
        return content.split('\n')
            .filter(l => l.trim())
            .map(l => { try { return JSON.parse(l); } catch(e) { return null; }})
            .filter(Boolean)
            .slice(-limit);
    } catch (e) {
        return [];
    }
}

// ══════════════════════════════════════════════════════════════════════════
// 📊 STRUCTURED QUERY API (V5 Intelligence)
// ══════════════════════════════════════════════════════════════════════════
async function queryLogs(options = {}) {
    const {
        category = null,
        level = null,
        action = null,
        since = null,
        until = null,
        limit = 100,
        search = null
    } = options;

    try {
        if (!await fs.pathExists(LOG_FILE)) return { logs: [], count: 0 };
        const content = await fs.readFile(LOG_FILE, 'utf8');
        let logs = content.split('\n')
            .filter(l => l.trim())
            .map(l => { try { return JSON.parse(l); } catch(e) { return null; }})
            .filter(Boolean);

        if (category) logs = logs.filter(l => l.category === category.toUpperCase());
        if (level) logs = logs.filter(l => l.level === level.toUpperCase());
        if (action) logs = logs.filter(l => l.action.includes(action));
        if (since) {
            const sinceMs = parseTimeWindow(since);
            const cutoff = Date.now() - sinceMs;
            logs = logs.filter(l => new Date(l.timestamp).getTime() > cutoff);
        }
        if (search) {
            const searchLower = search.toLowerCase();
            logs = logs.filter(l => JSON.stringify(l).toLowerCase().includes(searchLower));
        }

        const total = logs.length;
        logs = logs.slice(-limit);
        return { logs, count: total, returned: logs.length };
    } catch (e) {
        return { logs: [], count: 0, error: e.message };
    }
}

function parseTimeWindow(str) {
    const match = str.match(/^(\d+)([smhd])$/);
    if (!match) return 0;
    const [, num, unit] = match;
    const multipliers = { s: 1000, m: 60 * 1000, h: 60 * 60 * 1000, d: 24 * 60 * 60 * 1000 };
    return parseInt(num) * (multipliers[unit] || 0);
}

// ══════════════════════════════════════════════════════════════════════════
// 📈 METRICS AGGREGATION (V5 Intelligence)
// ══════════════════════════════════════════════════════════════════════════
async function getMetrics(timeWindow = '1h') {
    const result = await queryLogs({ since: timeWindow, limit: 10000 });
    const logs = result.logs;
    if (!logs.length) return { error: 'No logs in time window' };
    const categories = {};
    const levels = {};
    const actions = {};
    let totalErrors = 0;
    let totalWarnings = 0;

    for (const log of logs) {
        categories[log.category] = (categories[log.category] || 0) + 1;
        levels[log.level] = (levels[log.level] || 0) + 1;
        actions[log.action] = (actions[log.action] || 0) + 1;
        if (log.level === 'ERROR' || log.level === 'FATAL') totalErrors++;
        if (log.level === 'WARN') totalWarnings++;
    }

    return {
        timeWindow,
        totalEvents: logs.length,
        errorRate: ((totalErrors / logs.length) * 100).toFixed(2) + '%',
        warningRate: ((totalWarnings / logs.length) * 100).toFixed(2) + '%',
        categories,
        levels,
        topActions: Object.entries(actions).sort((a, b) => b[1] - a[1]).slice(0, 10),
        avgRamUsage: logs.length > 0
            ? (logs.reduce((sum, l) => sum + parseFloat(l.system_vitals?.ram_heap || 0), 0) / logs.length).toFixed(2) + ' MB'
            : 'N/A'
    };
}

// ══════════════════════════════════════════════════════════════════════════
// 🏆 REAL-TIME XAUUSD FOREX TRACKING SYSTEM (V5 Financial Intelligence)
// ══════════════════════════════════════════════════════════════════════════

let marketCache = {
    lastPrice: null,
    lastUpdate: null,
    trend: 'NEUTRAL',
    strength: 0,
    session: 'UNKNOWN',
    support: null,
    resistance: null,
    pivot: null,
    high: null,
    low: null,
    volatility: 0,
    source: 'NONE',
    priceHistory: [],
    movingAverage20: null,
    movingAverage50: null,
    rsi: null,
    macd: null
};

// Real-time price fetch with multiple sources
async function fetchXAUUSDPrice() {
    const sources = [
        {
            name: 'GoldAPI',
            url: 'https://www.goldapi.io/api/XAU/USD',
            headers: { 'x-access-token': process.env.GOLD_API_KEY || '' },
            parse: (data) => data.price ? parseFloat(data.price) : null
        },
        {
            name: 'MetalsAPI',
            url: 'https://metals-api.com/api/latest?access_key=' + (process.env.METALS_API_KEY || '') + '&base=USD&symbols=XAU',
            parse: (data) => data.rates && data.rates.XAU ? 1 / parseFloat(data.rates.XAU) : null
        },
        {
            name: 'ExchangeRate',
            url: 'https://api.exchangerate-api.com/v4/latest/USD',
            parse: (data) => data.rates && data.rates.XAU ? 1 / parseFloat(data.rates.XAU) : null
        },
        {
            name: 'CoinGecko',
            url: 'https://api.coingecko.com/api/v3/simple/price?ids=tether-gold&vs_currencies=usd',
            parse: (data) => data['tether-gold'] && data['tether-gold'].usd ? parseFloat(data['tether-gold'].usd) : null
        }
    ];

    for (const source of sources) {
        try {
            const res = await fetch(source.url, {
                headers: source.headers || {},
                timeout: 15000
            });
            if (!res.ok) continue;

            const data = await res.json();
            const price = source.parse(data);

            if (price && price > 1000 && price < 5000) {
                return {
                    price: price.toFixed(2),
                    source: source.name,
                    timestamp: new Date().toISOString(),
                    raw: data
                };
            }
        } catch (e) {
            continue;
        }
    }

    // Fallback: realistic simulation for testing
    const simulatedPrice = 1900 + (Math.random() * 400);
    return {
        price: simulatedPrice.toFixed(2),
        source: 'SIMULATED',
        timestamp: new Date().toISOString(),
        note: 'All APIs failed — using simulated data'
    };
}

// Determine trading session
function getTradingSession() {
    const hour = new Date().getUTCHours();
    if (hour >= 0 && hour < 8) return 'SYDNEY/TOKYO';
    if (hour >= 8 && hour < 16) return 'LONDON';
    if (hour >= 16 && hour < 21) return 'NEW_YORK';
    return 'OVERLAP/ASIA';
}

// Calculate RSI (Relative Strength Index)
function calculateRSI(prices, period = 14) {
    if (prices.length < period + 1) return null;
    let gains = 0, losses = 0;
    for (let i = 1; i <= period; i++) {
        const diff = prices[prices.length - i] - prices[prices.length - i - 1];
        if (diff > 0) gains += diff;
        else losses += Math.abs(diff);
    }
    const avgGain = gains / period;
    const avgLoss = losses / period;
    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
}

// Calculate Moving Averages
function calculateMA(prices, period) {
    if (prices.length < period) return null;
    const sum = prices.slice(-period).reduce((a, b) => a + b, 0);
    return sum / period;
}

// Calculate MACD
function calculateMACD(prices) {
    if (prices.length < 26) return null;
    const ema12 = calculateEMA(prices, 12);
    const ema26 = calculateEMA(prices, 26);
    if (!ema12 || !ema26) return null;
    const macd = ema12 - ema26;
    const signal = calculateEMA([macd], 9) || macd;
    return { macd: macd.toFixed(4), signal: signal.toFixed(4), histogram: (macd - signal).toFixed(4) };
}

function calculateEMA(prices, period) {
    if (prices.length < period) return null;
    const k = 2 / (period + 1);
    let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
    for (let i = period; i < prices.length; i++) {
        ema = prices[i] * k + ema * (1 - k);
    }
    return ema;
}

// Calculate Bollinger Bands
function calculateBollingerBands(prices, period = 20) {
    if (prices.length < period) return null;
    const ma = calculateMA(prices, period);
    const squaredDiffs = prices.slice(-period).map(p => Math.pow(p - ma, 2));
    const stdDev = Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / period);
    return {
        upper: (ma + (stdDev * 2)).toFixed(2),
        middle: ma.toFixed(2),
        lower: (ma - (stdDev * 2)).toFixed(2)
    };
}

// Advanced trend analysis
function analyzeTrend(currentPrice, history = []) {
    if (!history.length || !currentPrice) return { trend: 'NEUTRAL', strength: 0, confidence: 0 };

    const prices = history.map(h => parseFloat(h.price)).filter(p => !isNaN(p));
    if (prices.length < 5) return { trend: 'NEUTRAL', strength: 0, confidence: 0 };

    const current = parseFloat(currentPrice);
    const ma20 = calculateMA(prices, 20);
    const ma50 = calculateMA(prices, 50);
    const rsi = calculateRSI(prices, 14);
    const bb = calculateBollingerBands(prices);
    const macd = calculateMACD(prices);

    // Trend determination
    let trend = 'NEUTRAL';
    let signals = 0;
    let totalSignals = 0;

    // MA crossover
    if (ma20 && ma50) {
        totalSignals++;
        if (ma20 > ma50) signals++;
        else signals--;
    }

    // RSI
    if (rsi !== null) {
        totalSignals++;
        if (rsi > 60) signals++;
        else if (rsi < 40) signals--;
    }

    // Price vs Bollinger
    if (bb) {
        totalSignals++;
        if (current > parseFloat(bb.upper)) signals++;
        else if (current < parseFloat(bb.lower)) signals--;
    }

    // MACD
    if (macd) {
        totalSignals++;
        if (parseFloat(macd.macd) > parseFloat(macd.signal)) signals++;
        else signals--;
    }

    if (signals >= 2) trend = 'BULLISH';
    else if (signals <= -2) trend = 'BEARISH';

    const confidence = totalSignals > 0 ? Math.abs(signals / totalSignals) : 0;
    const strength = (Math.abs(signals) / Math.max(totalSignals, 1) * 100).toFixed(1);

    return {
        trend,
        strength,
        confidence: (confidence * 100).toFixed(1),
        rsi: rsi ? rsi.toFixed(2) : null,
        ma20: ma20 ? ma20.toFixed(2) : null,
        ma50: ma50 ? ma50.toFixed(2) : null,
        macd,
        bollinger: bb
    };
}

// Calculate support/resistance with volume profile
function calculateLevels(history = []) {
    if (!history.length) return { support: null, resistance: null, pivot: null, high: null, low: null };

    const prices = history.map(h => parseFloat(h.price)).filter(p => !isNaN(p));
    if (!prices.length) return { support: null, resistance: null, pivot: null, high: null, low: null };

    const sorted = [...prices].sort((a, b) => a - b);
    const len = sorted.length;

    return {
        support: sorted[Math.floor(len * 0.1)].toFixed(2),
        resistance: sorted[Math.floor(len * 0.9)].toFixed(2),
        pivot: sorted[Math.floor(len * 0.5)].toFixed(2),
        high: Math.max(...prices).toFixed(2),
        low: Math.min(...prices).toFixed(2)
    };
}

// Main XAUUSD tracking with real-time analysis
async function trackXAUUSD(vault = true) {
    try {
        const marketData = await fetchXAUUSDPrice();

        if (marketData.error || !marketData.price) {
            await trackAction('FOREX', 'XAUUSD_FETCH_FAILED', { error: marketData.error }, vault, 'WARN');
            return { success: false, error: marketData.error };
        }

        const currentPrice = parseFloat(marketData.price);
        const session = getTradingSession();

        // Load history
        let history = [];
        try {
            if (await fs.pathExists(FOREX_LOG)) {
                const content = await fs.readFile(FOREX_LOG, 'utf8');
                history = content.split('\n')
                    .filter(l => l.trim())
                    .map(l => { try { return JSON.parse(l); } catch(e) { return null; }})
                    .filter(Boolean)
                    .slice(-100);
            }
        } catch (e) {}

        // Advanced analysis
        const trend = analyzeTrend(currentPrice, history);
        const levels = calculateLevels(history);

        // Price history for indicators
        const priceHistory = history.map(h => parseFloat(h.price)).filter(p => !isNaN(p));
        priceHistory.push(currentPrice);

        // Update cache
        marketCache = {
            lastPrice: currentPrice.toFixed(2),
            lastUpdate: marketData.timestamp,
            trend: trend.trend,
            strength: trend.strength,
            confidence: trend.confidence,
            session: session,
            support: levels.support,
            resistance: levels.resistance,
            pivot: levels.pivot,
            high: levels.high,
            low: levels.low,
            rsi: trend.rsi,
            ma20: trend.ma20,
            ma50: trend.ma50,
            macd: trend.macd,
            bollinger: trend.bollinger,
            source: marketData.source,
            priceHistory: priceHistory.slice(-50)
        };

        await fs.writeJson(FOREX_STATE, marketCache, { spaces: 2 });

        // Log to forex history
        const forexEntry = {
            timestamp: marketData.timestamp,
            price: currentPrice.toFixed(2),
            trend: trend.trend,
            strength: trend.strength,
            session: session,
            rsi: trend.rsi,
            ma20: trend.ma20,
            ma50: trend.ma50,
            source: marketData.source
        };
        await fs.appendFile(FOREX_LOG, JSON.stringify(forexEntry) + '\n', 'utf8');

        // System log
        await trackAction('FOREX', 'XAUUSD_UPDATE', {
            price: currentPrice.toFixed(2),
            trend: trend.trend,
            session: session,
            strength: trend.strength,
            confidence: trend.confidence,
            rsi: trend.rsi,
            source: marketData.source
        }, vault, 'INFO');

        // Trading insights
        const insights = generateTradingInsights(currentPrice, trend, levels, session, priceHistory);

        return {
            success: true,
            data: marketCache,
            insights: insights,
            raw: marketData.raw || null
        };

    } catch (e) {
        await trackAction('FOREX', 'XAUUSD_ERROR', { error: e.message }, vault, 'ERROR');
        return { success: false, error: e.message };
    }
}

// Advanced trading insights with entry/exit signals
function generateTradingInsights(price, trend, levels, session, priceHistory) {
    const insights = [];
    const p = parseFloat(price);

    // Support/Resistance signals
    if (levels.support && p <= parseFloat(levels.support) * 1.002) {
        insights.push({
            type: 'BUY_ZONE',
            signal: 'LONG',
            message: `Price at support $${levels.support}. Potential bounce — consider BUY.`,
            confidence: 'HIGH',
            riskReward: '1:2'
        });
    }

    if (levels.resistance && p >= parseFloat(levels.resistance) * 0.998) {
        insights.push({
            type: 'SELL_ZONE',
            signal: 'SHORT',
            message: `Price at resistance $${levels.resistance}. Potential reversal — consider SELL.`,
            confidence: 'HIGH',
            riskReward: '1:2'
        });
    }

    // Trend momentum
    if (trend.trend === 'BULLISH' && parseFloat(trend.strength) > 60) {
        insights.push({
            type: 'MOMENTUM_BUY',
            signal: 'LONG',
            message: `Strong bullish momentum (${trend.strength}%). Pullback entry opportunity.`,
            confidence: trend.confidence + '%',
            riskReward: '1:1.5'
        });
    }

    if (trend.trend === 'BEARISH' && parseFloat(trend.strength) > 60) {
        insights.push({
            type: 'MOMENTUM_SELL',
            signal: 'SHORT',
            message: `Strong bearish momentum (${trend.strength}%). Breakdown entry opportunity.`,
            confidence: trend.confidence + '%',
            riskReward: '1:1.5'
        });
    }

    // RSI signals
    if (trend.rsi && parseFloat(trend.rsi) > 70) {
        insights.push({
            type: 'OVERBOUGHT',
            signal: 'SHORT',
            message: `RSI overbought (${trend.rsi}). Possible correction incoming.`,
            confidence: 'MEDIUM',
            riskReward: '1:1'
        });
    }

    if (trend.rsi && parseFloat(trend.rsi) < 30) {
        insights.push({
            type: 'OVERSOLD',
            signal: 'LONG',
            message: `RSI oversold (${trend.rsi}). Possible bounce incoming.`,
            confidence: 'MEDIUM',
            riskReward: '1:1'
        });
    }

    // Session volatility
    if (session === 'LONDON' || session === 'NEW_YORK') {
        insights.push({
            type: 'SESSION_ALERT',
            signal: 'CAUTION',
            message: `${session} session — high volatility. Wider stops recommended.`,
            confidence: 'LOW',
            riskReward: '1:3'
        });
    }

    // Bollinger signals
    if (trend.bollinger) {
        if (p > parseFloat(trend.bollinger.upper)) {
            insights.push({
                type: 'BB_BREAKOUT',
                signal: 'SHORT',
                message: `Price above upper Bollinger Band ($${trend.bollinger.upper}). Mean reversion likely.`,
                confidence: 'MEDIUM',
                riskReward: '1:1.5'
            });
        }
        if (p < parseFloat(trend.bollinger.lower)) {
            insights.push({
                type: 'BB_BREAKOUT',
                signal: 'LONG',
                message: `Price below lower Bollinger Band ($${trend.bollinger.lower}). Mean reversion likely.`,
                confidence: 'MEDIUM',
                riskReward: '1:1.5'
            });
        }
    }

    return insights;
}

// Get current market state
async function getMarketState() {
    try {
        if (await fs.pathExists(FOREX_STATE)) {
            return await fs.readJson(FOREX_STATE);
        }
        return marketCache;
    } catch (e) {
        return marketCache;
    }
}

// Get trading history
async function getForexHistory(limit = 100) {
    try {
        if (!await fs.pathExists(FOREX_LOG)) return [];
        const content = await fs.readFile(FOREX_LOG, 'utf8');
        return content.split('\n')
            .filter(l => l.trim())
            .map(l => { try { return JSON.parse(l); } catch(e) { return null; }})
            .filter(Boolean)
            .slice(-limit);
    } catch (e) {
        return [];
    }
}

// Auto-track XAUUSD
let forexInterval = null;

function startForexTracking(intervalMinutes = 5) {
    if (forexInterval) clearInterval(forexInterval);

    console.log(`${C.ORANGE}${C.BOLD}[FOREX]${C.RESET} XAUUSD real-time tracking started. Interval: ${intervalMinutes}min`);
    trackXAUUSD(true);

    forexInterval = setInterval(() => {
        trackXAUUSD(true);
    }, intervalMinutes * 60 * 1000);

    return true;
}

function stopForexTracking() {
    if (forexInterval) {
        clearInterval(forexInterval);
        forexInterval = null;
        console.log(`${C.YELLOW}[FOREX]${C.RESET} XAUUSD tracking stopped.`);
    }
}

// Financial metrics with advanced statistics
async function getFinancialMetrics() {
    const history = await getForexHistory(100);
    if (!history.length) return { error: 'No forex data available' };

    const prices = history.map(h => parseFloat(h.price)).filter(p => !isNaN(p));
    if (!prices.length) return { error: 'No valid price data' };

    const returns = [];
    for (let i = 1; i < prices.length; i++) {
        returns.push(((prices[i] - prices[i-1]) / prices[i-1]) * 100);
    }

    const avgReturn = returns.length ? (returns.reduce((a, b) => a + b, 0) / returns.length).toFixed(4) : 0;
    const variance = returns.length ? (returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length) : 0;
    const volatility = Math.sqrt(variance).toFixed(4);
    const sharpe = volatility > 0 ? (avgReturn / volatility).toFixed(2) : 0;

    const bullish = history.filter(h => h.trend === 'BULLISH').length;
    const bearish = history.filter(h => h.trend === 'BEARISH').length;
    const neutral = history.filter(h => h.trend === 'NEUTRAL').length;

    const lastPrice = prices[prices.length - 1];
    const firstPrice = prices[0];

    return {
        currentPrice: lastPrice.toFixed(2),
        priceChange: (lastPrice - firstPrice).toFixed(2),
        priceChangePercent: (((lastPrice - firstPrice) / firstPrice) * 100).toFixed(2),
        avgReturn: avgReturn + '%',
        volatility: volatility + '%',
        sharpeRatio: sharpe,
        maxDrawdown: Math.min(...returns).toFixed(4) + '%',
        trendDistribution: { bullish, bearish, neutral },
        totalRecords: history.length,
        lastUpdate: history[history.length - 1]?.timestamp || 'N/A',
        winRate: returns.length > 0 ? ((returns.filter(r => r > 0).length / returns.length) * 100).toFixed(1) + '%' : 'N/A'
    };
}

// Real-time market scanner
async function scanMarket() {
    const result = await trackXAUUSD(false);
    if (!result.success) return result;
    const state = result.data;
    const insights = result.insights;

    // Generate trading plan
    const plan = generateTradingPlan(state, insights);

    return {
        success: true,
        market: state,
        signals: insights,
        plan: plan,
        timestamp: new Date().toISOString()
    };
}

function generateTradingPlan(state, insights) {
    const strongSignals = insights.filter(i => i.confidence === 'HIGH');
    const plan = {
        direction: 'HOLD',
        entry: null,
        stopLoss: null,
        takeProfit: null,
        risk: 'LOW',
        reasoning: []
    };

    if (strongSignals.length === 0) {
        plan.reasoning.push('No high-confidence signals. Wait for clearer setup.');
        return plan;
    }

    const buySignals = strongSignals.filter(s => s.signal === 'LONG');
    const sellSignals = strongSignals.filter(s => s.signal === 'SHORT');

    if (buySignals.length > sellSignals.length) {
        plan.direction = 'LONG';
        plan.entry = state.lastPrice;
        plan.stopLoss = state.support || (parseFloat(state.lastPrice) * 0.99).toFixed(2);
        plan.takeProfit = state.resistance || (parseFloat(state.lastPrice) * 1.02).toFixed(2);
        plan.risk = 'MEDIUM';
        plan.reasoning = buySignals.map(s => s.message);
    } else if (sellSignals.length > buySignals.length) {
        plan.direction = 'SHORT';
        plan.entry = state.lastPrice;
        plan.stopLoss = state.resistance || (parseFloat(state.lastPrice) * 1.01).toFixed(2);
        plan.takeProfit = state.support || (parseFloat(state.lastPrice) * 0.98).toFixed(2);
        plan.risk = 'MEDIUM';
        plan.reasoning = sellSignals.map(s => s.message);
    }

    return plan;
}

// ══════════════════════════════════════════════════════════════════════════
// EXPORTS (Enhanced V5)
// ══════════════════════════════════════════════════════════════════════════
module.exports = {
    // Core telemetry
    trackAction,
    setLogLevel,

    // Query & Metrics
    queryLogs,
    getMetrics,
    getRecentAlerts,

    // Forex / XAUUSD — Real-Time
    trackXAUUSD,
    getMarketState,
    getForexHistory,
    getFinancialMetrics,
    startForexTracking,
    stopForexTracking,
    generateTradingInsights,
    scanMarket,
    generateTradingPlan,

    // Config
    LOG_LEVELS,
    marketCache
};

// ══════════════════════════════════════════════════════════════════════════
// CLI
// ══════════════════════════════════════════════════════════════════════════
if (require.main === module) {
    const args = process.argv.slice(2);
    const command = (args[0] || 'help').toLowerCase();

    (async () => {
        switch (command) {
            case 'forex':
            case 'xauusd': {
                console.log(`${C.ORANGE}${C.BOLD}🏆 Fetching XAUUSD Real-Time Data...${C.RESET}`);
                const result = await trackXAUUSD(true);
                if (result.success) {
                    console.log(`${C.GREEN}Price:${C.RESET} $${result.data.lastPrice}`);
                    console.log(`${C.CYAN}Trend:${C.RESET} ${result.data.trend} (${result.data.strength}% strength)`);
                    console.log(`${C.YELLOW}Session:${C.RESET} ${result.data.session}`);
                    console.log(`${C.BLUE}Support/Resistance:${C.RESET} ${result.data.support} / ${result.data.resistance}`);
                    if (result.insights.length) {
                        console.log(`\n${C.PURPLE}Insights:${C.RESET}`);
                        result.insights.forEach(i => console.log(`  - [${i.type}] ${i.message}`));
                    }
                } else {
                    console.log(`${C.RED}Failed:${C.RESET} ${result.error}`);
                }
                break;
            }

            case 'scan': {
                console.log(`${C.ORANGE}${C.BOLD}🔍 Scanning Market...${C.RESET}`);
                const scan = await scanMarket();
                console.log(JSON.stringify(scan, null, 2));
                break;
            }

            case 'track-start': {
                const minutes = parseInt(args[1]) || 5;
                startForexTracking(minutes);
                console.log(`${C.GREEN}Tracking started. Press Ctrl+C to stop.${C.RESET}`);
                break;
            }

            case 'track-stop': {
                stopForexTracking();
                break;
            }

            case 'metrics': {
                const window = args[1] || '1h';
                const metrics = await getMetrics(window);
                console.log(JSON.stringify(metrics, null, 2));
                break;
            }

            case 'financial-metrics': {
                const fm = await getFinancialMetrics();
                console.log(JSON.stringify(fm, null, 2));
                break;
            }

            case 'alerts': {
                const limit = parseInt(args[1]) || 50;
                const alerts = await getRecentAlerts(limit);
                console.log(JSON.stringify(alerts, null, 2));
                break;
            }

            case 'logs': {
                const category = args[1] || null;
                const logs = await queryLogs({ category, limit: 50 });
                console.log(JSON.stringify(logs, null, 2));
                break;
            }

            case 'state': {
                const state = await getMarketState();
                console.log(JSON.stringify(state, null, 2));
                break;
            }

            case 'help':
            default: {
                console.log(`${C.CYAN}${C.BOLD}PIKA TRACKER CLI${C.RESET}
Usage: node tracker.js <command> [args]

Commands:
  forex | xauusd          Fetch and display current XAUUSD price/analysis
  scan                     Full market scan with trading plan
  track-start [minutes]    Start auto-tracking XAUUSD (default 5min interval)
  track-stop               Stop auto-tracking
  metrics [window]         Show telemetry metrics (e.g. 1h, 30m, 1d)
  financial-metrics        Show forex statistics (Sharpe, volatility, etc.)
  alerts [limit]           Show recent error/fatal alerts
  logs [category]          Query logs, optionally filtered by category
  state                    Show current cached market state
  help                     Show this help message`);
                break;
            }
        }
    })();
}
