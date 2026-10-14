// ╔══════════════════════════════════════════════════════>
// ║   🤖 PIKA — LOGIC FACTORY ENGINE v5.1 GROQ-ONLY      >
// ║   15-Key Round-Robin · 1-Min Rate Limit · Queue       >
// ║   Auto-Continuation · Zero Local Dependencies          >
// ╚══════════════════════════════════════════════════════>
'use strict';

const fs   = require('fs');
const path = require('path');

// ═══════════════════════════════════════════════════════>
// FETCH POLYFILL (Node 16/17 compatible)
// ═══════════════════════════════════════════════════════>
let fetch;
try {
    fetch = require('node-fetch');
} catch (e) {
    fetch = globalThis.fetch;
    if (!fetch) {
        console.error('[FATAL] fetch not available. Install node-fetch or use Node 18+.');
        process.exit(1);
    }
}

// ═══════════════════════════════════════════════════════>
// LOAD .env (supports GROQ_API_KEY_1 ... GROQ_API_KEY_15)
// ═══════════════════════════════════════════════════════>
(function loadEnv() {
    const envPath = path.resolve(process.cwd(), '.env');
    if (!fs.existsSync(envPath)) return;
    fs.readFileSync(envPath, 'utf8')
        .split('\n')
        .forEach(line => {
            const m = line.match(/^\s*([\w.-]+)\s*=\s*(.*)$/);
            if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim();
        });
})();

// ═══════════════════════════════════════════════════════>
// ANSI Terminal Colors
// ═══════════════════════════════════════════════════════>
const C = {
    RESET:    '\x1b[0m',
    RED:      '\x1b[31m',
    GREEN:    '\x1b[32m',
    YELLOW:   '\x1b[33m',
    CYAN:     '\x1b[36m',
    MAGENTA:  '\x1b[35m',
    BLUE:     '\x1b[34m',
    WHITE:    '\x1b[37m',
    BOLD:     '\x1b[1m',
    DIM:      '\x1b[2m',
};

const banner = (msg, color = C.CYAN) =>
    console.log(`${color}${C.BOLD}▶ ${msg}${C.RESET}`);

const engineLog = (msg, status = 'info') => {
    const colors = { info: C.CYAN, ok: C.GREEN, warn: C.YELLOW, error: C.RED, shift: C.MAGENTA };
    const icon   = { info: 'ℹ', ok: '✓', warn: '⚠', error: '✗', shift: '↻' };
    console.log(`${colors[status] || C.CYAN}[GROQ] ${icon[status] || 'ℹ'} ${msg}${C.RESET}`);
};

// ═══════════════════════════════════════════════════════>
// CONFIGURATION — GROQ ONLY
// ═══════════════════════════════════════════════════════>
const CONFIG = {
    MAX_RETRIES:         3,
    CHUNK_TIMEOUT:       300000,
    RUNTIME_TIMEOUT:     2500,
    CACHE_ENABLED:       true,
    BACKUP_DIR:          'backups',
    HIT_INTERVAL_MS:     60000, // ← 1 minute gap between API hits

    GROQ: {
        API_URL:    'https://api.groq.com/openai/v1/chat/completions',
        MODEL:      'llama3-70b-8192',
        MAX_TOKENS: 4096,
    },
};

// ═══════════════════════════════════════════════════════>
// 15-KEY ROUND-ROBIN POOL
// ═══════════════════════════════════════════════════════>
function loadGroqKeys() {
    const keys = [];
    
    // Pattern 1: GROQ_API_KEY_1 through GROQ_API_KEY_15
    for (let i = 1; i <= 15; i++) {
        const k = process.env[`GROQ_API_KEY_${i}`];
        if (k) keys.push(k);
    }
    
    // Pattern 2: Comma-separated GROQ_API_KEYS
    if (process.env.GROQ_API_KEYS) {
        keys.push(...process.env.GROQ_API_KEYS.split(',').map(k => k.trim()).filter(Boolean));
    }
    
    // Pattern 3: Single fallback GROQ_API_KEY
    if (process.env.GROQ_API_KEY && !keys.includes(process.env.GROQ_API_KEY)) {
        keys.push(process.env.GROQ_API_KEY);
    }
    
    const unique = [...new Set(keys)];
    if (unique.length === 0) {
        console.error(`${C.RED}[FATAL] No Groq API keys found.${C.RESET}`);
        console.error(`${C.RED}        Set in .env: GROQ_API_KEY_1=xxx ... GROQ_API_KEY_15=xxx${C.RESET}`);
        console.error(`${C.RED}        OR: GROQ_API_KEYS=key1,key2,key3${C.RESET}`);
        process.exit(1);
    }
    
    banner(`Loaded ${unique.length} Groq key(s) — Round-Robin active`, C.GREEN);
    return unique;
}

const GROQ_KEY_POOL = loadGroqKeys();

class KeyRotator {
    constructor(keys) {
        this.keys = keys;
        this.index = 0;
        this.keyStats = new Map(keys.map(k => [k.slice(-8), { success: 0, fail: 0 }]));
    }
    
    next() {
        const key = this.keys[this.index % this.keys.length];
        this.index++;
        return key;
    }
    
    reportSuccess(key) {
        const s = this.keyStats.get(key.slice(-8));
        if (s) s.success++;
    }
    
    reportFail(key) {
        const s = this.keyStats.get(key.slice(-8));
        if (s) s.fail++;
    }
    
    stats() {
        return Array.from(this.keyStats.entries()).map(([k, v]) => ({ key: `...${k}`, ...v }));
    }
}

const keyRotator = new KeyRotator(GROQ_KEY_POOL);

// ═══════════════════════════════════════════════════════>
// LRU CACHE
// ═══════════════════════════════════════════════════════>
class LRUCache {
    constructor(maxSize = 100, ttlMs = 30 * 60 * 1000) {
        this.maxSize = maxSize;
        this.ttlMs = ttlMs;
        this.cache = new Map();
        this.timestamps = new Map();
    }
    get(key) {
        const ts = this.timestamps.get(key);
        if (ts && Date.now() - ts > this.ttlMs) {
            this.delete(key);
            return undefined;
        }
        if (this.cache.has(key)) {
            const val = this.cache.get(key);
            this.cache.delete(key);
            this.cache.set(key, val);
            return val;
        }
        return undefined;
    }
    set(key, value) {
        if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
            const firstKey = this.cache.keys().next().value;
            this.delete(firstKey);
        }
        this.cache.set(key, value);
        this.timestamps.set(key, Date.now());
    }
    has(key) { return this.get(key) !== undefined; }
    delete(key) {
        this.cache.delete(key);
        this.timestamps.delete(key);
    }
    clear() {
        this.cache.clear();
        this.timestamps.clear();
    }
}

const cognitiveCache = new LRUCache(100, 30 * 60 * 1000);

// ═══════════════════════════════════════════════════════>
// FETCH WITH TIMEOUT
// ═══════════════════════════════════════════════════════>
async function fetchWithTimeout(url, opts = {}, timeoutMs = CONFIG.CHUNK_TIMEOUT) {
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
        const res = await fetch(url, { ...opts, signal: ctrl.signal });
        return res;
    } finally {
        clearTimeout(tid);
    }
}

// ═══════════════════════════════════════════════════════>
// GROQ API CALL
// ═══════════════════════════════════════════════════════>
async function askGroq(messages, opts = {}) {
    const key = opts.apiKey || keyRotator.next();
    const maxTokens = opts.maxTokens || CONFIG.GROQ.MAX_TOKENS;
    
    const res = await fetchWithTimeout(
        CONFIG.GROQ.API_URL,
        {
            method: 'POST',
            headers: {
                'Content-Type':  'application/json',
                'Authorization': `Bearer ${key}`,
            },
            body: JSON.stringify({
                model:       opts.model || CONFIG.GROQ.MODEL,
                messages:    messages,
                temperature: opts.temperature ?? 0.2,
                max_tokens:  maxTokens,
            }),
        },
        opts.timeout || CONFIG.CHUNK_TIMEOUT
    );

    if (!res.ok) {
        const body = await res.text().catch(() => '');
        throw new Error(`Groq HTTP ${res.status}: ${body.slice(0, 200)}`);
    }

    const data = await res.json();
    const content = data?.choices?.[0]?.message?.content || '';
    const usage = data?.usage || {};
    const finishReason = data?.choices?.[0]?.finish_reason || '';
    
    return {
        content,
        usage,
        finishReason,
        key,
        truncated: finishReason === 'length' || (usage?.completion_tokens >= maxTokens - 10),
    };
}

// ═══════════════════════════════════════════════════════>
// TASK QUEUE — 1 HIT PER MINUTE
// ═══════════════════════════════════════════════════════>
class TaskQueue {
    constructor() {
        this.queue = [];
        this.processing = false;
        this.lastHitTime = 0;
        this.activeTasks = new Map();
        this.taskIdCounter = 0;
        this._shutdown = false;
    }
    
    sleep(ms) {
        return new Promise(r => setTimeout(r, ms));
    }
    
    generateId() {
        return `task-${++this.taskIdCounter}-${Date.now()}`;
    }
    
    // Add a new task
    enqueue(prompt, opts = {}) {
        const id = this.generateId();
        const task = {
            id,
            prompt,
            opts,
            status: 'pending',
            result: '',
            attempts: 0,
            createdAt: Date.now(),
            messages: [{ role: 'user', content: prompt }],
        };
        this.queue.push(task);
        this.activeTasks.set(id, task);
        engineLog(`Task ${id} queued | Queue size: ${this.queue.length}`, 'info');
        this.startProcessor();
        return id;
    }
    
    getTask(id) {
        return this.activeTasks.get(id);
    }
    
    // Detect incomplete response
    isIncomplete(response, finishReason) {
        if (!response) return true;
        if (finishReason === 'length') return true;
        
        const trimmed = response.trim();
        
        // Odd number of ``` means unclosed code block
        const fences = (trimmed.match(/```/g) || []).length;
        if (fences % 2 !== 0) return true;
        
        // Ends with ellipsis or dash
        if (/(\.\.\.|…|--|-)\s*$/.test(trimmed)) return true;
        
        // Ends mid-sentence (heuristic)
        if (/[a-zA-Z0-9_,;:\s]$/.test(trimmed)) {
            if (!trimmed.endsWith('```') && !trimmed.endsWith('}') && !trimmed.endsWith(');')) {
                if (!/[.!?]"?'?\s*$/.test(trimmed)) return true;
            }
        }
        
        return false;
    }
    
    async startProcessor() {
        if (this.processing) return;
        this.processing = true;
        
        while (this.queue.length > 0 && !this._shutdown) {
            const now = Date.now();
            const elapsed = now - this.lastHitTime;
            const wait = Math.max(0, CONFIG.HIT_INTERVAL_MS - elapsed);
            
            if (wait > 0) {
                engineLog(`Rate limit active | Next hit in ${Math.ceil(wait/1000)}s | Pending: ${this.queue.length}`, 'warn');
                await this.sleep(wait);
            }
            
            const task = this.queue.shift();
            await this.processTask(task);
        }
        
        this.processing = false;
        if (!this._shutdown) {
            engineLog('Queue empty. Processor idle.', 'ok');
        }
    }
    
    async processTask(task) {
        task.status = 'running';
        task.attempts++;
        
        const key = keyRotator.next();
        engineLog(`Task ${task.id} | Attempt ${task.attempts} | Key ...${key.slice(-8)} | Messages: ${task.messages.length}`, 'info');
        
        try {
            this.lastHitTime = Date.now();
            const response = await askGroq(task.messages, { ...task.opts, apiKey: key });
            
            task.result += response.content;
            task.finishReason = response.finishReason;
            task.usage = response.usage;
            
            keyRotator.reportSuccess(key);
            engineLog(`Task ${task.id} | Got ${response.content.length} chars | reason=${response.finishReason}`, 'ok');
            
            // Incomplete? → Re-queue for continuation (waits next minute automatically)
            if (this.isIncomplete(task.result, response.finishReason)) {
                engineLog(`Task ${task.id} | Incomplete response. Will continue in next minute slot...`, 'warn');
                task.messages.push({ role: 'assistant', content: response.content });
                task.messages.push({
                    role: 'user',
                    content: 'Continue exactly from where you left off. Do NOT repeat anything already written. Just continue.'
                });
                task.status = 'pending_continuation';
                this.queue.push(task);
            } else {
                task.status = 'completed';
                task.completedAt = Date.now();
                engineLog(`Task ${task.id} | COMPLETED | Total: ${task.result.length} chars | Attempts: ${task.attempts}`, 'ok');
                
                if (task.opts.cacheKey && CONFIG.CACHE_ENABLED) {
                    cognitiveCache.set(task.opts.cacheKey, task.result);
                }
            }
            
        } catch (err) {
            keyRotator.reportFail(key);
            engineLog(`Task ${task.id} | Error: ${err.message}`, 'error');
            
            if (task.attempts < CONFIG.MAX_RETRIES) {
                engineLog(`Task ${task.id} | Re-queueing for retry ${task.attempts}/${CONFIG.MAX_RETRIES}`, 'warn');
                task.status = 'pending';
                this.queue.push(task);
            } else {
                task.status = 'failed';
                task.error = err.message;
                engineLog(`Task ${task.id} | FAILED after ${task.attempts} attempts`, 'error');
            }
        }
    }
    
    // Continue a running/pending task manually
    continueTask(id) {
        const task = this.activeTasks.get(id);
        if (!task || task.status === 'completed' || task.status === 'failed') return false;
        task.messages.push({ role: 'user', content: 'Please continue from where you left off.' });
        task.status = 'pending';
        this.queue.push(task);
        this.startProcessor();
        return true;
    }
    
    list() {
        return Array.from(this.activeTasks.values()).map(t => ({
            id: t.id,
            status: t.status,
            attempts: t.attempts,
            resultLength: t.result.length,
            createdAt: t.createdAt,
            completedAt: t.completedAt,
        }));
    }
    
    shutdown() {
        this._shutdown = true;
        engineLog('Shutdown signal received. Finishing current task...', 'warn');
    }
}

const taskQueue = new TaskQueue();

// ═══════════════════════════════════════════════════════>
// MAIN API
// ═══════════════════════════════════════════════════════>
async function cognitiveEngine(prompt, opts = {}) {
    const cacheKey = opts.cacheKey || null;
    
    if (cacheKey && CONFIG.CACHE_ENABLED && cognitiveCache.has(cacheKey)) {
        engineLog(`Cache hit → ${cacheKey}`, 'ok');
        return cognitiveCache.get(cacheKey);
    }
    
    const taskId = taskQueue.enqueue(prompt, { ...opts, cacheKey });
    
    // Sync wait mode (default)
    if (opts.wait !== false) {
        return new Promise((resolve, reject) => {
            const check = setInterval(() => {
                const task = taskQueue.getTask(taskId);
                if (!task) {
                    clearInterval(check);
                    reject(new Error('Task disappeared from queue'));
                    return;
                }
                if (task.status === 'completed') {
                    clearInterval(check);
                    resolve(task.result);
                }
                if (task.status === 'failed') {
                    clearInterval(check);
                    reject(new Error(task.error || 'Task failed'));
                }
            }, 1000);
            
            if (opts.totalTimeout) {
                setTimeout(() => {
                    clearInterval(check);
                    reject(new Error(`Task ${taskId} timed out after ${opts.totalTimeout}ms`));
                }, opts.totalTimeout);
            }
        });
    }
    
    return taskId; // Async mode: return task ID
}

// ═══════════════════════════════════════════════════════>
// UTILITIES (from original)
// ═══════════════════════════════════════════════════════>
function extractCode(raw) {
    const fenceMatch = raw.match(/```(?:javascript|js|typescript|ts|node)?\n?([\s\S]*?)```/);
    let cleaned = fenceMatch ? fenceMatch[1] : raw;
    cleaned = cleaned
        .replace(/^(?:Here's|This is|The following|Below is|Sure[,!]?).*?:\s*/im, '')
        .replace(/^\s*\n/, '');
    cleaned = cleaned
        .split('\n')
        .filter(line => {
            const t = line.trim();
            if (!t) return false;
            if (t.match(/^(Let me|I'll|To |This |The |You can|Here is|Note:|Important:|Warning:|Explanation:)/i)) {
                return false;
            }
            return true;
        })
        .join('\n')
        .trim();
    return cleaned;
}

function parseJSON(text, fallback = []) {
    try { return JSON.parse(text); } catch (_) {}
    const m = text.match(/\[[\s\S]*\]|\{[\s\S]*\}/);
    if (m) { try { return JSON.parse(m[0]); } catch (_) {} }
    return fallback;
}

async function ensureBackupDir() {
    const dir = path.resolve(process.cwd(), CONFIG.BACKUP_DIR);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    return dir;
}

async function backupFile(filePath) {
    const abs = path.resolve(process.cwd(), filePath);
    if (!fs.existsSync(abs))
        return { success: true, backupPath: null, note: 'New file — no backup needed' };
    try {
        const dir = await ensureBackupDir();
        const ext = path.extname(abs);
        const base = path.basename(abs, ext);
        const ts = new Date().toISOString().replace(/[:.]/g, '-');
        const bkpPath = path.join(dir, `${base}.${ts}.backup${ext}`);
        await new Promise((res, rej) => {
            const rs = fs.createReadStream(abs);
            const ws = fs.createWriteStream(bkpPath);
            rs.on('error', rej);
            ws.on('error', rej);
            ws.on('finish', res);
            rs.pipe(ws);
        });
        console.log(`${C.GREEN}[BACKUP] ✓ → ${bkpPath}${C.RESET}`);
        return { success: true, backupPath: bkpPath };
    } catch (err) {
        return { success: false, error: err.message };
    }
}

// ═══════════════════════════════════════════════════════>
// STATUS DASHBOARD
// ═══════════════════════════════════════════════════════>
function printStatus() {
    console.log(`\n${C.CYAN}${C.BOLD}╔══════════════════════════════════════════════════════╗${C.RESET}`);
    console.log(`${C.CYAN}${C.BOLD}║        PIKA GROQ-ONLY ENGINE v5.1 STATUS             ║${C.RESET}`);
    console.log(`${C.CYAN}${C.BOLD}╠══════════════════════════════════════════════════════╣${C.RESET}`);
    
    const tasks = taskQueue.list();
    const pending = tasks.filter(t => t.status === 'pending' || t.status === 'pending_continuation').length;
    const running = tasks.filter(t => t.status === 'running').length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const failed = tasks.filter(t => t.status === 'failed').length;
    
    console.log(`${C.CYAN}║  Keys:      ${GROQ_KEY_POOL.length.toString().padEnd(36)}║${C.RESET}`);
    console.log(`${C.CYAN}║  Pending:   ${pending.toString().padEnd(36)}║${C.RESET}`);
    console.log(`${C.CYAN}║  Running:   ${running.toString().padEnd(36)}║${C.RESET}`);
    console.log(`${C.CYAN}║  Completed: ${completed.toString().padEnd(36)}║${C.RESET}`);
    console.log(`${C.CYAN}║  Failed:    ${failed.toString().padEnd(36)}║${C.RESET}`);
    console.log(`${C.CYAN}║  Cache:     ${cognitiveCache.cache.size.toString().padEnd(36)}║${C.RESET}`);
    console.log(`${C.CYAN}${C.BOLD}╠══════════════════════════════════════════════════════╣${C.RESET}`);
    console.log(`${C.CYAN}║  KEY          SUCCESS    FAILED                      ║${C.RESET}`);
    console.log(`${C.CYAN}${C.BOLD}╠══════════════════════════════════════════════════════╣${C.RESET}`);
    
    keyRotator.stats().forEach(s => {
        const line = `  ...${s.key}     ${s.success.toString().padStart(3)}      ${s.fail.toString().padStart(3)}`;
        console.log(`${C.CYAN}║${line.padEnd(52)}║${C.RESET}`);
    });
    
    console.log(`${C.CYAN}${C.BOLD}╚══════════════════════════════════════════════════════╝${C.RESET}\n`);
}

// ═══════════════════════════════════════════════════════>
// EXPORTS
// ═══════════════════════════════════════════════════════>
module.exports = {
    cognitiveEngine,
    taskQueue,
    cognitiveCache,
    extractCode,
    parseJSON,
    backupFile,
    printStatus,
    CONFIG,
    C,
    banner,
    engineLog,
};

// ═══════════════════════════════════════════════════════>
// CLI
// ═══════════════════════════════════════════════════════>
if (require.main === module) {
    banner('PIKA Logic Factory v5.1 — Groq-Only Mode', C.GREEN);
    printStatus();
    
    const prompt = process.argv[2];
    if (prompt) {
        banner(`Submitting task...`, C.YELLOW);
        cognitiveEngine(prompt, { cacheKey: `cli-${Date.now()}` })
            .then(result => {
                console.log(`\n${C.GREEN}══════════ RESULT ══════════${C.RESET}`);
                console.log(result);
                console.log(`${C.GREEN}════════════════════════════${C.RESET}`);
                printStatus();
                process.exit(0);
            })
            .catch(err => {
                console.error(`${C.RED}[ERROR] ${err.message}${C.RESET}`);
                process.exit(1);
            });
    } else {
        console.log(`${C.DIM}Usage: node logic_factory.js "your prompt"${C.RESET}`);
        console.log(`${C.DIM}Queue runs 1 task/minute. Pending tasks stay alive.${C.RESET}`);
    }
}
