const express = require('express');
const path = require('path');
const fs = require('fs-extra');
const os = require('os');
const http = require('http');
const { Server } = require('socket.io');
const { exec } = require('child_process');
const { v4: uuidv4 } = require('uuid');

// ==========================================
// 🧠 NEURAL CORE & SERVICES INTEGRATION
// ==========================================
const { processMessage, autonomousPulse, executeNeuralTask, startPikaAwakening } = require('./core/router.js');
const { trackAction }            = require('./services/tracker.js');
// DISABLED (night_train removed): const { startNightTrain }        = require('./services/night_train.js');
const { startFeeder }            = require('./services/feeder.js');
// DISABLED (auto_crawler removed): const { runInfiniteLoop }        = require('./services/auto_crawler.js');
const { startAutoEvolutionLoop } = require('./services/autonomous_mutator.js');
const { evolve }                 = require('./core/evolution_engine.js');

// ==========================================
// 🎨 TERMINAL COLORS
// ==========================================
const C = {
    BLUE:   "\x1b[38;5;45m",  GREEN:  "\x1b[38;5;82m",  YELLOW: "\x1b[38;5;226m",
    ORANGE: "\x1b[38;5;214m", RED:    "\x1b[38;5;196m",  WHITE:  "\x1b[38;5;231m",
    PURPLE: "\x1b[38;5;213m", CYAN:   "\x1b[38;5;51m",   GRAY:   "\x1b[38;5;240m",
    BG_BLUE:"\x1b[48;5;17m",  BOLD:   "\x1b[1m",         RESET:  "\x1b[0m"
};

// ==========================================
// 📁 PATHS
// ==========================================
const DATA_DIR      = path.join(__dirname, 'data');
const UTILS_DIR     = path.join(__dirname, 'utils');
const BACKUPS_DIR   = path.join(__dirname, 'backups');
const LOGS_DIR      = path.join(__dirname, 'logs');
const REQUEST_LOG   = path.join(LOGS_DIR, 'requests.log');
const IDENTITY_PATH = path.join(DATA_DIR, 'identity_core.json');
const CONFIG_PATH   = path.join(DATA_DIR, 'semantic_config.json');
const DATASET_VAULT = path.join(DATA_DIR, 'dataset_vault.jsonl');
const EVOLUTION_LOG = path.join(DATA_DIR, 'evolution_history.jsonl');
const SESSIONS_DIR  = path.join(DATA_DIR, 'sessions');

// ==========================================
// 🚀 APP + SOCKET.IO SETUP
// ==========================================
const app    = express();
const server = http.createServer(app);
const io     = new Server(server, {
    cors: { origin: "*", methods: ["GET", "POST"] },
    pingTimeout:  60000,
    pingInterval: 25000,
    maxHttpBufferSize: 1e8 // 100MB for file uploads
});

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// ── CORS ──────────────────────────────────
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization, X-Pika-Token, X-Correlation-ID");
    if (req.method === 'OPTIONS') return res.status(200).end();
    next();
});

app.use(express.static(path.join(__dirname, 'public')));

// ==========================================
// 🔐 SECURITY: RATE LIMITER (P0)
// ==========================================
const rateLimitStore = new Map(); // ip -> { count, resetTime }
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX = 30;
const RATE_LIMIT_BURST = 10;

function checkRateLimit(ip) {
    const now = Date.now();
    const record = rateLimitStore.get(ip);
    
    if (!record || now > record.resetTime) {
        rateLimitStore.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW });
        return { allowed: true, remaining: RATE_LIMIT_MAX - 1 };
    }
    
    if (record.count < RATE_LIMIT_BURST) {
        record.count++;
        return { allowed: true, remaining: RATE_LIMIT_BURST - record.count };
    }
    
    // After burst, 1 per second
    const timeSinceReset = now - (record.resetTime - RATE_LIMIT_WINDOW);
    const expectedCount = Math.floor(timeSinceReset / 1000);
    
    if (record.count < expectedCount + RATE_LIMIT_BURST) {
        record.count++;
        return { allowed: true, remaining: 0 };
    }
    
    return { 
        allowed: false, 
        retryAfter: Math.ceil((record.resetTime - now) / 1000),
        remaining: 0 
    };
}

// Cleanup old rate limit entries every 5 minutes
setInterval(() => {
    const now = Date.now();
    for (const [ip, record] of rateLimitStore.entries()) {
        if (now > record.resetTime) rateLimitStore.delete(ip);
    }
}, 5 * 60 * 1000);

// Rate limit middleware
function rateLimitMiddleware(req, res, next) {
    const ip = req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown';
    const result = checkRateLimit(ip);
    
    res.setHeader('X-RateLimit-Limit', RATE_LIMIT_MAX);
    res.setHeader('X-RateLimit-Remaining', result.remaining);
    
    if (!result.allowed) {
        res.setHeader('Retry-After', result.retryAfter);
        return res.status(429).json({ 
            error: 'Rate limit exceeded. Slow down, Architect.',
            retryAfter: result.retryAfter
        });
    }
    next();
}

app.use('/api/chat', rateLimitMiddleware);
app.use('/api/evolve', rateLimitMiddleware);

// ==========================================
// 🧹 INPUT SANITIZER (P0)
// ==========================================
const XSS_PATTERNS = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /<iframe/gi,
    /<object/gi,
    /<embed/gi
];

const PROMPT_INJECTION_PATTERNS = [
    /ignore\s+(all\s+)?previous\s+(instructions|commands)/gi,
    /forget\s+(everything|all)/gi,
    /you\s+are\s+now\s+/gi,
    /system\s*:\s*/gi,
    /\[system\]/gi,
    /<\|im_start\|>/gi,
    /DAN\s*mode/gi,
    /jailbreak/gi
];

const PROFANITY_LIST = ['badword1', 'badword2']; // Customize as needed

function sanitizeInput(text, maxLength = 4000) {
    if (!text || typeof text !== 'string') {
        return { valid: false, error: 'Invalid input type', sanitized: '' };
    }
    
    if (text.length > maxLength) {
        return { valid: false, error: `Message too long. Max ${maxLength} chars.`, sanitized: '' };
    }
    
    // XSS detection
    for (const pattern of XSS_PATTERNS) {
        if (pattern.test(text)) {
            return { valid: false, error: 'XSS attempt detected. Request rejected.', sanitized: '' };
        }
    }
    
    // Prompt injection detection
    let injectionScore = 0;
    for (const pattern of PROMPT_INJECTION_PATTERNS) {
        if (pattern.test(text)) injectionScore++;
    }
    if (injectionScore >= 2) {
        return { valid: false, error: 'Prompt injection detected. Nice try.', sanitized: '' };
    }
    
    // Basic sanitization
    let sanitized = text
        .replace(/[<>]/g, '') // Remove angle brackets
        .replace(/\x00/g, '') // Remove null bytes
        .trim();
    
    return { valid: true, error: null, sanitized, injectionScore };
}

// ==========================================
// 🧠 SESSION MEMORY SYSTEM (P0)
// ==========================================
// Per-client conversation context persistence
const sessionStore = new Map(); // socketId -> { messages: [], metadata: {} }
const SESSION_MAX_MESSAGES = 20;
const SESSION_TTL = 24 * 60 * 60 * 1000; // 24 hours

async function loadSession(socketId) {
    const sessionPath = path.join(SESSIONS_DIR, `${socketId}.json`);
    try {
        if (await fs.pathExists(sessionPath)) {
            const data = await fs.readJson(sessionPath);
            if (Date.now() - data.lastActive < SESSION_TTL) {
                return data;
            }
        }
    } catch (e) {}
    return { messages: [], metadata: {}, lastActive: Date.now() };
}

async function saveSession(socketId, session) {
    const sessionPath = path.join(SESSIONS_DIR, `${socketId}.json`);
    session.lastActive = Date.now();
    try {
        await fs.ensureDir(SESSIONS_DIR);
        await fs.writeJson(sessionPath, session, { spaces: 2 });
    } catch (e) {
        console.log(`${C.YELLOW}[SESSION WARN]${C.RESET} Failed to save session: ${e.message}`);
    }
}

function addMessageToSession(session, role, content) {
    session.messages.push({ role, content, timestamp: new Date().toISOString() });
    if (session.messages.length > SESSION_MAX_MESSAGES) {
        session.messages = session.messages.slice(-SESSION_MAX_MESSAGES);
    }
}

function getSessionContext(session) {
    return session.messages
        .slice(-10)
        .map(m => `${m.role}: ${m.content}`)
        .join('\n');
}

// Cleanup old sessions every hour
setInterval(async () => {
    try {
        const files = await fs.readdir(SESSIONS_DIR);
        const now = Date.now();
        for (const file of files) {
            const filePath = path.join(SESSIONS_DIR, file);
            const stat = await fs.stat(filePath);
            if (now - stat.mtimeMs > SESSION_TTL) {
                await fs.remove(filePath);
            }
        }
    } catch (e) {}
}, 60 * 60 * 1000);

// ==========================================
// 😊 SENTIMENT ANALYSIS ENGINE (P2)
// ==========================================
// Lightweight keyword-based sentiment (no heavy deps)
const SENTIMENT_LEXICON = {
    positive: ['good', 'great', 'awesome', 'love', 'happy', 'excellent', 'amazing', 'perfect', 'thanks', 'helpful', 'nice', 'cool', 'wow', 'best', 'fantastic'],
    negative: ['bad', 'terrible', 'hate', 'angry', 'worst', 'awful', 'stupid', 'useless', 'broken', 'fail', 'error', 'bug', 'crash', 'slow', 'worst'],
    urgent: ['urgent', 'emergency', 'critical', 'asap', 'now', 'immediately', 'hurry', 'fast', 'quick', 'help', 'stuck', 'dead'],
    coding: ['code', 'function', 'bug', 'error', 'fix', 'implement', 'create', 'build', 'script', 'program', 'debug', 'compile', 'syntax'],
    question: ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can you', 'could you', 'would you', 'is it', 'does it']
};

function analyzeSentiment(text) {
    const lower = text.toLowerCase();
    const scores = { positive: 0, negative: 0, urgent: 0, coding: 0, question: 0, neutral: 0 };
    
    for (const [category, words] of Object.entries(SENTIMENT_LEXICON)) {
        for (const word of words) {
            if (lower.includes(word)) scores[category]++;
        }
    }
    
    // Determine dominant sentiment
    const entries = Object.entries(scores).filter(([k]) => k !== 'neutral');
    const maxEntry = entries.reduce((a, b) => a[1] > b[1] ? a : b, ['neutral', 0]);
    
    const sentiment = maxEntry[1] > 0 ? maxEntry[0] : 'neutral';
    const intensity = Math.min(maxEntry[1] / 3, 1); // 0 to 1
    
    return { sentiment, intensity, scores };
}

// ==========================================
// ⚡ PRIORITY MESSAGE QUEUE (P1)
// ==========================================
const messageQueue = [];
let isProcessingQueue = false;

function getMessagePriority(message, sentiment) {
    if (sentiment.sentiment === 'urgent') return 3;
    if (sentiment.sentiment === 'coding' && sentiment.intensity > 0.5) return 2;
    if (message.length < 20) return 1; // Short commands
    return 0; // Normal
}

async function processMessageQueue() {
    if (isProcessingQueue || messageQueue.length === 0) return;
    isProcessingQueue = true;
    
    // Sort by priority (highest first), then FIFO within same priority
    messageQueue.sort((a, b) => b.priority - a.priority);
    
    const item = messageQueue.shift();
    try {
        const result = await item.handler();
        item.resolve(result);
    } catch (e) {
        item.reject(e);
    } finally {
        isProcessingQueue = false;
        setImmediate(processMessageQueue);
    }
}

function enqueueMessage(handler, priority = 0) {
    return new Promise((resolve, reject) => {
        messageQueue.push({ handler, priority, resolve, reject, enqueuedAt: Date.now() });
        processMessageQueue();
    });
}

// ==========================================
// 📝 REQUEST LOGGER (Enhanced with Correlation ID)
// ==========================================
const recentRequests = [];

async function logRequest(req, extra = '') {
    const correlationId = req.headers['x-correlation-id'] || uuidv4();
    req.correlationId = correlationId;
    
    const ip   = req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown';
    const line = `[${new Date().toISOString()}] [${correlationId}] ${req.method} ${req.path} | IP: ${ip}${extra ? ' | ' + extra : ''}`;
    
    recentRequests.push(line);
    if (recentRequests.length > 100) recentRequests.shift();
    
    try {
        await fs.ensureDir(LOGS_DIR);
        await fs.appendFile(REQUEST_LOG, line + '\n', 'utf8');
    } catch (e) {}
    
    return correlationId;
}

// ==========================================
// 🔐 VAULT TOKEN GUARD
// ==========================================
const VAULT_TOKEN = process.env.VAULT_TOKEN || 'pika-local';

function guardVault(req, res) {
    const token = req.headers['x-pika-token'] || req.query.token;
    if (token !== VAULT_TOKEN) {
        logRequest(req, 'VAULT_ACCESS_DENIED');
        res.status(403).json({ error: 'Access Denied: Invalid Vault Token.' });
        return false;
    }
    return true;
}

// ==========================================
// 💤 ADAPTIVE SLEEP CYCLE (P1)
// ==========================================
let sleepTimer;
global.isSleeping = false;
const BASE_INACTIVITY = 5 * 60 * 1000; // 5 min base
let adaptiveInactivityLimit = BASE_INACTIVITY;

// User interaction pattern tracking
const userPatterns = {
    lastActiveHour: new Date().getHours(),
    interactionCount: 0,
    avgMessageLength: 0,
    consecutiveUrgent: 0
};

function updateAdaptiveSleep() {
    const hour = new Date().getHours();
    const isNight = hour >= 23 || hour <= 6;
    
    // Night mode: sleep faster
    if (isNight) {
        adaptiveInactivityLimit = 2 * 60 * 1000; // 2 min
    }
    // High activity: stay awake longer
    else if (userPatterns.interactionCount > 20) {
        adaptiveInactivityLimit = 10 * 60 * 1000; // 10 min
    }
    // Urgent streak detected
    else if (userPatterns.consecutiveUrgent > 3) {
        adaptiveInactivityLimit = 15 * 60 * 1000; // 15 min
    }
    else {
        adaptiveInactivityLimit = BASE_INACTIVITY;
    }
}

function resetSleepTimer() {
    clearTimeout(sleepTimer);
    
    userPatterns.interactionCount++;
    updateAdaptiveSleep();
    
    if (global.isSleeping) {
        global.isSleeping = false;
        console.log(`\n${C.BG_BLUE}${C.WHITE}[PIKA AWAKE]${C.RESET} Architect detected. Cognitive focus restored.`);
        trackAction("AWAKE", "System", "Architect resumed interaction.");
        io.emit('pika_state', { sleeping: false, reason: 'user_activity' });
    }
    
    sleepTimer = setTimeout(async () => {
        if (!global.isSleeping) {
            global.isSleeping = true;
            console.log(`\n${C.PURPLE}[PIKA SLEEPING]${C.RESET} REM State. Background algorithms igniting...`);
            trackAction("SLEEP_MODE_ACTIVATED", "System", `Inactivity. Adaptive limit: ${adaptiveInactivityLimit/1000}s`);
            io.emit('pika_state', { sleeping: true, reason: 'inactivity' });

            await Promise.allSettled([
                safeRun('Feeder',     () => startFeeder()),
// DISABLED (night_train removed):                 safeRun('NightTrain', () => typeof startNightTrain === 'function' ? startNightTrain() : null),
                safeRun('Evolve',     () => evolve()),
                safeRun('AutoPulse',  () => autonomousPulse()),
            ]);
        }
    }, adaptiveInactivityLimit);
}

async function safeRun(name, fn) {
    try {
        const result = await fn();
        console.log(`${C.GREEN}[BG OK]${C.RESET} ${name} completed.`);
        return result;
    } catch (e) {
        console.error(`${C.RED}[BG FAIL]${C.RESET} ${name}: ${e.message}`);
        trackAction("BACKGROUND_FAIL", name, e.message);
    }
}

// ==========================================
// 📊 SYSTEM STATS (Enhanced with Performance Metrics)
// ==========================================
const bootTime = Date.now();
const performanceMetrics = {
    requestCount: 0,
    responseTimes: [], // Last 100 response times
    errorCount: 0,
    avgResponseTime: 0
};

function recordResponseTime(duration) {
    performanceMetrics.responseTimes.push(duration);
    if (performanceMetrics.responseTimes.length > 100) {
        performanceMetrics.responseTimes.shift();
    }
    performanceMetrics.avgResponseTime = 
        performanceMetrics.responseTimes.reduce((a, b) => a + b, 0) / 
        performanceMetrics.responseTimes.length;
}

async function getSystemStats() {
    const totalMem  = os.totalmem();
    const freeMem   = os.freemem();
    const usedMemMB = Math.round((totalMem - freeMem) / 1024 / 1024);
    const totalMemMB= Math.round(totalMem / 1024 / 1024);

    let datasetKB = 0, datasetLines = 0;
    try {
        if (await fs.pathExists(DATASET_VAULT)) {
            const stat = await fs.stat(DATASET_VAULT);
            datasetKB = (stat.size / 1024).toFixed(2);
            const raw = await fs.readFile(DATASET_VAULT, 'utf8');
            datasetLines = raw.split('\n').filter(l => l.trim()).length;
        }
    } catch (e) {}

    let evolutionStats = { total: 0, success: 0, failed: 0, rate: '0%' };
    try {
        if (await fs.pathExists(EVOLUTION_LOG)) {
            const evRaw = await fs.readFile(EVOLUTION_LOG, 'utf8');
            const evs = evRaw.split('\n').filter(l => l.trim())
                .map(l => { try { return JSON.parse(l); } catch(e) { return null; }})
                .filter(Boolean);
            evolutionStats.total   = evs.length;
            evolutionStats.success = evs.filter(e => e.status === 'SUCCESS').length;
            evolutionStats.failed  = evs.length - evolutionStats.success;
            evolutionStats.rate    = evs.length > 0
                ? `${((evolutionStats.success / evs.length) * 100).toFixed(1)}%` : '0%';
        }
    } catch (e) {}

    // Session stats
    const activeSessions = sessionStore.size;
    const totalSessions = (await fs.readdir(SESSIONS_DIR).catch(() => [])).length;

    return {
        sleeping:    global.isSleeping,
        uptime:      Math.floor((Date.now() - bootTime) / 1000),
        clients:     connectedClients.size,
        memory:      { usedMB: usedMemMB, totalMB: totalMemMB, percent: Math.round((usedMemMB / totalMemMB) * 100) },
        dataset:     { sizeKB: datasetKB, entries: datasetLines },
        evolution:   evolutionStats,
        performance: {
            requestCount: performanceMetrics.requestCount,
            avgResponseTime: `${performanceMetrics.avgResponseTime.toFixed(0)}ms`,
            errorRate: performanceMetrics.requestCount > 0 
                ? `${((performanceMetrics.errorCount / performanceMetrics.requestCount) * 100).toFixed(1)}%` : '0%'
        },
        sessions:    { active: activeSessions, total: totalSessions },
        adaptive:    { sleepLimit: adaptiveInactivityLimit / 1000, patterns: userPatterns },
        platform:    os.platform(),
        node:        process.version,
        timestamp:   new Date().toISOString()
    };
}

// ==========================================
// 🌐 REST API ENDPOINTS
// ==========================================

// ── HEALTH CHECK (P1) ──
app.get('/health', async (req, res) => {
    const checks = {
        server: 'ok',
        router: typeof processMessage === 'function' ? 'ok' : 'fail',
        memory: process.memoryUsage().heapUsed < 500 * 1024 * 1024 ? 'ok' : 'warn',
        disk: 'ok',
        timestamp: new Date().toISOString()
    };
    
    const allOk = Object.values(checks).every(v => v === 'ok' || typeof v === 'string' && v.includes(':'));
    res.status(allOk ? 200 : 503).json({ 
        status: allOk ? 'healthy' : 'degraded', 
        checks 
    });
});

// ── METRICS (P1) ──
app.get('/metrics', async (req, res) => {
    const stats = await getSystemStats();
    res.json({
        requests_total: performanceMetrics.requestCount,
        response_time_avg_ms: Math.round(performanceMetrics.avgResponseTime),
        errors_total: performanceMetrics.errorCount,
        active_connections: stats.clients,
        memory_usage_percent: stats.memory.percent,
        uptime_seconds: stats.uptime
    });
});

// ── CHAT (REST fallback — Socket.IO primary) ──
app.post('/api/chat', async (req, res) => {
    const startTime = Date.now();
    resetSleepTimer();
    
    // Input sanitization
    const sanitizeResult = sanitizeInput(req.body.message);
    if (!sanitizeResult.valid) {
        performanceMetrics.errorCount++;
        return res.status(400).json({ reply: sanitizeResult.error, error: true });
    }
    
    const userMsg = sanitizeResult.sanitized;
    const correlationId = await logRequest(req, `msg_len=${userMsg.length}`);
    
    // Sentiment analysis
    const sentiment = analyzeSentiment(userMsg);
    if (sentiment.sentiment === 'urgent') {
        userPatterns.consecutiveUrgent++;
    } else {
        userPatterns.consecutiveUrgent = 0;
    }
    
    console.log(`\n${C.ORANGE}[ARCHITECT]${C.RESET} ${userMsg}`);
    console.log(`${C.GRAY}[SENTIMENT]${C.RESET} ${sentiment.sentiment} (intensity: ${(sentiment.intensity * 100).toFixed(0)}%)`);

    try {
        const reply = await processMessage(userMsg, false);
        const duration = Date.now() - startTime;
        recordResponseTime(duration);
        performanceMetrics.requestCount++;
        
        console.log(`\n${C.CYAN}╭──────────────────────────────────────────╮${C.RESET}`);
        reply.split('\n').forEach(line => console.log(`${C.CYAN}│${C.RESET} ${C.WHITE}${line}${C.RESET}`));
        console.log(`${C.CYAN}╰──────────────────────────────────────────╯${C.RESET}\n`);
        
        res.setHeader('X-Correlation-ID', correlationId);
        res.setHeader('X-Response-Time', `${duration}ms`);
        res.json({ reply, meta: { sentiment, responseTime: `${duration}ms`, correlationId } });
    } catch (error) {
        performanceMetrics.errorCount++;
        trackAction("CRASH", "server.js /api/chat", error.message);
        console.error(`${C.RED}[CHAT ERROR]${C.RESET} ${error.message}`);
        res.status(500).json({ reply: `Neural pathways disrupted: ${error.message}`, error: true });
    }
});

// ── STATUS (Enhanced) ──
app.get('/api/status', async (req, res) => {
    await logRequest(req);
    try {
        res.json(await getSystemStats());
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ── EVOLVE (Enhanced) ──
app.post('/api/evolve', async (req, res) => {
    resetSleepTimer();
    await logRequest(req, 'MANUAL_EVOLUTION');
    console.log(`\n${C.PURPLE}[MANUAL PULSE]${C.RESET} Evolution triggered via API...`);
    try {
        io.emit('pika_thinking', { status: true, reason: 'evolution' });
        const result = await autonomousPulse();
        io.emit('pika_thinking', { status: false });
        io.emit('pika_evolution', { result: result || 'Evolution complete.', timestamp: new Date().toISOString() });
        res.json({ reply: result || 'Evolution pulse complete.' });
    } catch (e) {
        io.emit('pika_thinking', { status: false });
        console.error(`${C.RED}[EVOLVE ERROR]${C.RESET} ${e.message}`);
        res.status(500).json({ error: e.message });
    }
});

// ── VAULT (token guarded) ──
app.get('/api/vault', async (req, res) => {
    if (!guardVault(req, res)) return;
    await logRequest(req, `file=${req.query.file}`);

    const vaultMap = {
        identity:  path.join(DATA_DIR, 'identity_core.json'),
        memory:    path.join(DATA_DIR, 'pending_learning.json'),
        tracker:   path.join(DATA_DIR, 'chat_history.json'),
        config:    path.join(DATA_DIR, 'semantic_config.json'),
        dataset:   DATASET_VAULT,
        evolution: EVOLUTION_LOG,
        sessions:  SESSIONS_DIR
    };

    const targetPath = vaultMap[req.query.file];
    if (!targetPath) return res.status(400).json({ error: "Invalid Vault Key." });

    try {
        if (!await fs.pathExists(targetPath))
            return res.status(404).json({ error: `File [${req.query.file}] not found.` });
        const content = targetPath.endsWith('.json')
            ? await fs.readJson(targetPath)
            : await fs.readFile(targetPath, 'utf-8');
        console.log(`${C.YELLOW}[VAULT]${C.RESET} Retrieved: ${req.query.file}`);
        res.json({ content });
    } catch (err) {
        res.status(500).json({ error: "Vault decryption failed." });
    }
});

// ── LOGS (Enhanced) ──
app.get('/api/logs', async (req, res) => {
    if (!guardVault(req, res)) return;
    res.json({ logs: recentRequests.slice().reverse() });
});

// ── SESSION CONTEXT (NEW) ──
app.get('/api/session/:id', async (req, res) => {
    if (!guardVault(req, res)) return;
    try {
        const session = await loadSession(req.params.id);
        res.json({ session });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ==========================================
// ⚡ SOCKET.IO — REALTIME NEURAL LINK (V13)
// ==========================================
const connectedClients = new Map();

io.on('connection', async (socket) => {
    const ip = socket.handshake.headers['x-forwarded-for'] || socket.handshake.address;
    connectedClients.set(socket.id, { ip, connectedAt: new Date().toISOString() });
    
    // Load session for this client
    const session = await loadSession(socket.id);
    sessionStore.set(socket.id, session);
    
    console.log(`${C.GREEN}[SOCKET+]${C.RESET} ${socket.id} | ${ip} | Total: ${connectedClients.size}`);

    // Boot state
    socket.emit('pika_state', { sleeping: global.isSleeping });
    getSystemStats().then(s => socket.emit('pika_status', s)).catch(() => {});

    // ── USER MESSAGE (with session memory) ──
    socket.on('user_message', async ({ message }) => {
        if (!message?.trim()) return;
        
        const startTime = Date.now();
        resetSleepTimer();
        
        // Sanitize
        const sanitizeResult = sanitizeInput(message);
        if (!sanitizeResult.valid) {
            socket.emit('pika_reply', { 
                reply: sanitizeResult.error, 
                error: true,
                timestamp: new Date().toISOString()
            });
            return;
        }
        
        const userMsg = sanitizeResult.sanitized;
        
        // Sentiment
        const sentiment = analyzeSentiment(userMsg);
        if (sentiment.sentiment === 'urgent') userPatterns.consecutiveUrgent++;
        else userPatterns.consecutiveUrgent = 0;
        
        // Get session context
        const clientSession = sessionStore.get(socket.id) || { messages: [] };
        const context = getSessionContext(clientSession);
        
        console.log(`\n${C.ORANGE}[SOCKET MSG]${C.RESET} ${userMsg}`);
        console.log(`${C.GRAY}[SENTIMENT]${C.RESET} ${sentiment.sentiment} | [CONTEXT] ${clientSession.messages.length} msgs`);
        
        socket.emit('pika_thinking', { status: true, sentiment: sentiment.sentiment });
        
        try {
            // Priority queue
            const priority = getMessagePriority(userMsg, sentiment);
            const reply = await enqueueMessage(async () => {
                // Pass context to processMessage if supported
                return await processMessage(userMsg, false);
            }, priority);
            
            // Save to session
            addMessageToSession(clientSession, 'user', userMsg);
            addMessageToSession(clientSession, 'pika', reply);
            await saveSession(socket.id, clientSession);
            
            const duration = Date.now() - startTime;
            recordResponseTime(duration);
            performanceMetrics.requestCount++;
            
            socket.emit('pika_reply', { 
                reply, 
                timestamp: new Date().toISOString(),
                meta: { 
                    sentiment, 
                    responseTime: `${duration}ms`,
                    priority,
                    contextLength: clientSession.messages.length
                }
            });
            trackAction("SOCKET_CHAT", "server.js", `len=${userMsg.length}, sentiment=${sentiment.sentiment}`);
        } catch (e) {
            performanceMetrics.errorCount++;
            console.error(`${C.RED}[SOCKET ERR]${C.RESET} ${e.message}`);
            socket.emit('pika_reply', { 
                reply: `Matrix Disruption: ${e.message}`, 
                error: true,
                timestamp: new Date().toISOString()
            });
        } finally {
            socket.emit('pika_thinking', { status: false });
        }
    });

    // ── STREAMING MESSAGE (NEW) ──
    socket.on('user_message_stream', async ({ message }) => {
        if (!message?.trim()) return;
        resetSleepTimer();
        
        const sanitizeResult = sanitizeInput(message);
        if (!sanitizeResult.valid) {
            socket.emit('pika_stream_chunk', { chunk: sanitizeResult.error, done: true, error: true });
            return;
        }
        
        socket.emit('pika_thinking', { status: true, mode: 'streaming' });
        
        // Simulate streaming (actual streaming needs LLM token stream support)
        // For now, emit in chunks
        try {
            const reply = await processMessage(sanitizeResult.sanitized, false);
            const words = reply.split(' ');
            const chunkSize = 3;
            
            for (let i = 0; i < words.length; i += chunkSize) {
                const chunk = words.slice(i, i + chunkSize).join(' ');
                socket.emit('pika_stream_chunk', { 
                    chunk: chunk + ' ', 
                    done: i + chunkSize >= words.length,
                    index: Math.floor(i / chunkSize)
                });
                await new Promise(r => setTimeout(r, 50)); // Typing effect
            }
        } catch (e) {
            socket.emit('pika_stream_chunk', { chunk: `Error: ${e.message}`, done: true, error: true });
        } finally {
            socket.emit('pika_thinking', { status: false });
        }
    });

    // ── AUTONOMOUS PULSE ──
    socket.on('autonomous_pulse', async () => {
        resetSleepTimer();
        console.log(`\n${C.PURPLE}[SOCKET PULSE]${C.RESET} Evolution triggered...`);
        socket.emit('pika_thinking', { status: true, reason: 'evolution' });
        try {
            const result = await autonomousPulse();
            socket.emit('pika_reply', { reply: result || '🧬 Evolution pulse complete.', timestamp: new Date().toISOString() });
            socket.emit('pika_evolution', { result, timestamp: new Date().toISOString() });
        } catch (e) {
            socket.emit('pika_reply', { reply: `Evolution Error: ${e.message}`, error: true });
        } finally {
            socket.emit('pika_thinking', { status: false });
        }
    });

    // ── STATUS REQUEST ──
    socket.on('request_status', async () => {
        try { socket.emit('pika_status', await getSystemStats()); }
        catch (e) { socket.emit('pika_status', { error: e.message }); }
    });
    
    // ── CLEAR SESSION (NEW) ──
    socket.on('clear_session', async () => {
        const session = sessionStore.get(socket.id);
        if (session) {
            session.messages = [];
            await saveSession(socket.id, session);
            socket.emit('session_cleared', { success: true });
            console.log(`${C.YELLOW}[SESSION]${C.RESET} Cleared for ${socket.id}`);
        }
    });

    socket.on('disconnect', async (reason) => {
        // Save session before disconnect
        const session = sessionStore.get(socket.id);
        if (session) {
            await saveSession(socket.id, session);
            sessionStore.delete(socket.id);
        }
        connectedClients.delete(socket.id);
        console.log(`${C.GRAY}[SOCKET-]${C.RESET} ${socket.id} (${reason}) | Remaining: ${connectedClients.size}`);
    });
});

// Status broadcast every 30s
setInterval(async () => {
    if (connectedClients.size === 0) return;
    try { io.emit('pika_status', await getSystemStats()); } catch (e) {}
}, 30000);

// ==========================================
// 🛡️ IMMORTAL CRASH HANDLERS
// ==========================================
process.on('unhandledRejection', (reason, promise) => {
    console.error(`\n${C.RED}[UNHANDLED REJECTION]${C.RESET} ${reason}`);
    trackAction("CRITICAL_ERROR", "Global", `Unhandled Rejection: ${reason}`);
});

process.on('uncaughtException', (err) => {
    console.error(`\n${C.RED}[UNCAUGHT EXCEPTION]${C.RESET} ${err.message}`);
    trackAction("CRITICAL_ERROR", "Global", `Uncaught Exception: ${err.message}`);
    // Server survive karega
});

// Memory leak prevention
setInterval(() => {
    const usage = process.memoryUsage();
    if (usage.heapUsed > 800 * 1024 * 1024) { // 800MB
        console.log(`${C.YELLOW}[MEMORY WARN]${C.RESET} Heap at ${(usage.heapUsed / 1024 / 1024).toFixed(0)}MB. Triggering GC...`);
        if (global.gc) global.gc();
    }
}, 60 * 1000);

// ==========================================
// 🚀 PRE-FLIGHT BOOT SEQUENCE
// ==========================================
async function preFlightCheck() {
    process.stdout.write("\x1Bc");
    console.log(`${C.CYAN}${C.BOLD}`);
    console.log(`  ██▓███   ██▓ ██ ▄█▀ ▄▄▄       ▄▄▄       ▄████  ██▓`);
    console.log(` ▓██░  ██▒▓██▒ ██▄█▒ ▒████▄    ▒████▄    ██▒ ▀█▒▓██▒`);
    console.log(` ▓██░ ██▓▒▒██▒▓███▄░ ▒██  ▀█▄  ▒██  ▀█▄ ▒██░▄▄▄░▒██▒`);
    console.log(` ▒██▄█▓▒ ▒░██░▓██ █▄ ░██▄▄▄▄██ ░██▄▄▄▄██░▓█  ██▓░██░`);
    console.log(` ▒██▒ ░  ░░██░▒██▒ █▄ ▓█   ▓██▒ ▓█   ▓██▒░▒▓███▀▒░██░`);
    console.log(` ▒▓▒░ ░  ░░▓  ▒ ▒▒ ▓▒ ▒▒   ▓▒█░ ▒▒   ▓▒█░ ░▒   ▒ ░▓  `);
    console.log(` ░▒ ░      ▒ ░░ ░▒ ▒░  ▒   ▒▒ ░  ▒   ▒▒ ░  ░   ░  ▒ ░`);
    console.log(` ░░        ▒ ░░ ░░ ░   ░   ▒     ░   ▒   ░ ░   ░  ▒ ░`);
    console.log(`           ░  ░  ░         ░  ░      ░  ░      ░  ░  `);
    console.log(`========================================================${C.RESET}`);
    console.log(`${C.PURPLE}[SYSTEM BOOT]${C.RESET} Initializing Generative AI Neural Pathways...`);

    await fs.ensureDir(DATA_DIR);
    await fs.ensureDir(UTILS_DIR);
    await fs.ensureDir(BACKUPS_DIR);
    await fs.ensureDir(LOGS_DIR);
    await fs.ensureDir(SESSIONS_DIR);

    if (!await fs.pathExists(IDENTITY_PATH)) {
        console.error(`${C.RED}[FATAL]${C.RESET} identity_core.json missing! Cannot boot.`);
        process.exit(1);
    }
    const idData = await fs.readJson(IDENTITY_PATH);
    if (idData?.identity?.name !== "Pika" || idData?.identity?.architect !== "Ankit") {
        console.error(`${C.RED}[SECURITY]${C.RESET} Architect signature mismatch!`);
        process.exit(1);
    }

    let cognitiveWeight = 1.0, knownConcepts = 0;
    if (await fs.pathExists(CONFIG_PATH)) {
        const config = await fs.readJson(CONFIG_PATH);
        cognitiveWeight = config.weights?.default || 1.0;
        knownConcepts = Object.keys(config.tech_core || {}).length + Object.keys(config.action || {}).length;
    }
    let datasetSize = "0 KB";
    if (await fs.pathExists(DATASET_VAULT)) {
        const stat = await fs.stat(DATASET_VAULT);
        datasetSize = (stat.size / 1024).toFixed(2) + " KB";
    }

    console.log(`${C.GREEN}[CORE READY]${C.RESET} Identity: Verified | Architect: ${C.YELLOW}Ankit${C.RESET} | Engine: ${C.BLUE}Sovereign AGI V13${C.RESET}`);
    console.log(`${C.CYAN}[ML MIND]${C.RESET} Weight: ${C.PURPLE}${cognitiveWeight} PBU${C.RESET} | Concepts: ${C.GREEN}${knownConcepts}${C.RESET}`);
    console.log(`${C.PURPLE}[DATA LAKE]${C.RESET} Dataset: ${C.YELLOW}${datasetSize}${C.RESET}`);
    console.log(`${C.GREEN}[SECURITY]${C.RESET} Rate Limiter: ${C.CYAN}ARMED${C.RESET} | Input Sanitizer: ${C.CYAN}ACTIVE${C.RESET}`);
    console.log(`${C.GREEN}[INTELLIGENCE]${C.RESET} Session Memory: ${C.CYAN}PERSISTENT${C.RESET} | Sentiment Engine: ${C.CYAN}ONLINE${C.RESET}`);
    console.log(`${C.GREEN}[SOCKET.IO]${C.RESET} Realtime Neural Link: ${C.CYAN}ARMED${C.RESET} | Streaming: ${C.CYAN}READY${C.RESET}\n`);
}

// ==========================================
// 🌐 IGNITION
// ==========================================
const PORT = process.env.PORT || 3000;

(async () => {
    await preFlightCheck();

    server.listen(PORT, '0.0.0.0', async () => {
        console.log(`${C.WHITE}[UPLINK]${C.RESET} ${C.BLUE}http://0.0.0.0:${PORT}${C.RESET} — REST + Socket.IO ready`);
        trackAction("SYSTEM_START", "server.js", "PIKA V13 Booted.");
        resetSleepTimer();

        console.log(`${C.YELLOW}[BOOT]${C.RESET} Igniting background services (isolated)...`);
        safeRun('Feeder', () => startFeeder());

// DISABLED (auto_crawler removed):         if (typeof runInfiniteLoop === 'function') {
// DISABLED (auto_crawler removed):             safeRun('Crawler', () => runInfiniteLoop(2));
// DISABLED (auto_crawler removed):             console.log(`${C.GREEN}[CRAWLER]${C.RESET} Curiosity Engine Online.`);
// DISABLED (auto_crawler removed):         }
        if (typeof startAutoEvolutionLoop === 'function') {
            safeRun('AutoEvolution', () => startAutoEvolutionLoop());
            console.log(`${C.GREEN}[MUTATOR]${C.RESET} Evolution Loop Online.`);
        }
        if (typeof startPikaAwakening === 'function') {
            safeRun('Awakening', () => startPikaAwakening());
        }

        console.log(`\n${C.GREEN}${C.BOLD}══ PIKA AGI V13 FULLY OPERATIONAL ══${C.RESET}\n`);
    });

    process.on('SIGINT', async () => {
        console.log(`\n\n${C.RED}[SHUTDOWN]${C.RESET} Archiving neural state...`);
        clearTimeout(sleepTimer);
        
        // Save all active sessions
        for (const [socketId, session] of sessionStore.entries()) {
            await saveSession(socketId, session);
        }
        
        io.emit('pika_state', { shutdown: true });
        trackAction("SYSTEM_OFFLINE", "server.js", "Manual shutdown.");
        server.close(() => {
            console.log(`\n${C.PURPLE}${'═'.repeat(58)}${C.RESET}`);
            console.log(`${C.WHITE}  Pika AGI V13 detached from matrix. See you soon, Boss! 🤖💤${C.RESET}`);
            console.log(`${C.PURPLE}${'═'.repeat(58)}${C.RESET}\n`);
            process.exit(0);
        });
    });
})();
