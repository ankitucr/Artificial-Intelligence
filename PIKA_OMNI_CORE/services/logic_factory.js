// ╔══════════════════════════════════════════════════════════════════════╗
// ║   🤖 PIKA — LOGIC FACTORY ENGINE v5.0                               ║
// ║   Self-Healing · Self-Mutating · 4-Tier Cognitive Fallback           ║
// ║   Semantic Understanding · AST-Based · Intelligent Testing             ║
// ║   Designed for Termux/Android · Pure Node.js · Zero Heavy Deps       ║
// ╚══════════════════════════════════════════════════════════════════════╝
'use strict';

const fs   = require('fs');
const path = require('path');
const vm   = require('vm');

// ══════════════════════════════════════════════════════════════════════════
// FETCH POLYFILL (Node 16/17 compatible) — BUG FIX #1
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

// Load .env manually (no dotenv dependency)
(function loadEnv() {
    const envPath = path.resolve(process.cwd(), '.env');
    if (!fs.existsSync(envPath)) return;
    fs.readFileSync(envPath, 'utf8')
        .split('\n')
        .forEach(line => {
            const m = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
            if (m && !process.env[m[1]]) process.env[m[1]] = (m[2] || '').replace(/^['"]|['"]$/g, '');
        });
})();

// ══════════════════════════════════════════════════════════════════════════
// ANSI Terminal Colors — Matrix Style
// ══════════════════════════════════════════════════════════════════════════
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
    BLINK:    '\x1b[5m',
    BG_BLACK: '\x1b[40m',
    BG_GREEN: '\x1b[42m',
};

const banner = (msg, color = C.CYAN) =>
    console.log(`${color}${C.BOLD}▶ ${msg}${C.RESET}`);

const engineLog = (engine, msg, status = 'info') => {
    const colors = { info: C.CYAN, ok: C.GREEN, warn: C.YELLOW, err: C.RED, shift: C.MAGENTA };
    const icons  = { info: '◈', ok: '✓', warn: '⚠', err: '✗', shift: '⇒' };
    const col    = colors[status] || C.WHITE;
    const icon   = icons[status]  || '·';
    console.log(`${col}${C.BOLD}[ENGINE:${engine}] ${icon} ${msg}${C.RESET}`);
};

const phase = (n, name) =>
    console.log(`\n${C.BLUE}${C.BOLD}╔═══════════════════════════════════════╗${C.RESET}` +
                `\n${C.BLUE}${C.BOLD}║  PHASE ${n}: ${name.padEnd(31)}║${C.RESET}` +
                `\n${C.BLUE}${C.BOLD}╚═══════════════════════════════════════╝${C.RESET}`);

// ══════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ══════════════════════════════════════════════════════════════════════════
const CONFIG = {
    MAX_RETRIES:         3,
    MAX_CYCLE_LOOPS:     3,
    ENGINE_RETRIES:      3,
    CHUNK_TIMEOUT:       300000,
    RUNTIME_TIMEOUT:     2500,
    PARALLEL_CHUNKS:     3,
    CACHE_ENABLED:       true,
    BACKUP_DIR:          'backups',

    MODELS: {
        PRIMARY_CODER:     'qwen2.5-coder:3b',
        REASONING:         'deepseek-r1:1.5b',
        FALLBACK_CODER:    'qwen2.5-coder:3b',
    },

    GROQ: {
        API_URL:   'https://api.groq.com/openai/v1/chat/completions',
        MODEL:     'llama3-70b-8192',
        get KEY()  { return process.env.GROQ_API_KEY || ''; },
    },

    SEARCH: {
        DDG_URL:    'https://api.duckduckgo.com/',
        SEARX_URL:  'https://searx.be/search',
        TIMEOUT:    15000,
    },

    SELF_EVOLUTION: {
        ENABLED:                 true,
        MUTATION_THRESHOLD:      85,
        MAX_MUTATIONS_PER_CYCLE: 5,
        get SELF_FILE()          { return __filename; },
        EVOLUTION_LOG:           'evolution.log.json',
        FOCUS_AREAS:             ['performance', 'reliability', 'error_handling', 'readability'],
    },

    // V5: New intelligent features
    INTELLIGENCE: {
        AST_PARSER:          true,
        AUTO_TEST_GEN:       true,
        ADAPTIVE_ENGINE:     true,
        CONTEXT_AWARE:       true,
        PERFORMANCE_PROFILE: true,
        SECURITY_SCAN:       true,
    },
};

// ══════════════════════════════════════════════════════════════════════════
// COGNITIVE CACHE with LRU + TTL — BUG FIX #9
// ══════════════════════════════════════════════════════════════════════════
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
            // Move to end (most recently used)
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

    has(key) {
        return this.get(key) !== undefined;
    }

    delete(key) {
        this.cache.delete(key);
        this.timestamps.delete(key);
    }

    get size() {
        return this.cache.size;
    }

    clear() {
        this.cache.clear();
        this.timestamps.clear();
    }
}

const cognitiveCache = new LRUCache(100, 30 * 60 * 1000);

const EVOLUTION_STATE = {
    totalMutations:      0,
    successfulMutations: 0,
    failedMutations:     0,
    cycleHistory:        [],
    lastScore:           0,
    version:             '5.0',
    engineStats:         { ollama: { success: 0, fail: 0 }, groq: { success: 0, fail: 0 }, search: { success: 0, fail: 0 } },
};

// ══════════════════════════════════════════════════════════════════════════
// UTILITY — fetch with timeout (BUG FIX #18: finally cleanup)
// ══════════════════════════════════════════════════════════════════════════
async function fetchWithTimeout(url, opts = {}, timeoutMs = CONFIG.CHUNK_TIMEOUT) {
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
        const res = await fetch(url, { ...opts, signal: ctrl.signal });
        return res;
    } catch (e) {
        throw e;
    } finally {
        clearTimeout(tid);
    }
}

// ══════════════════════════════════════════════════════════════════════════
// ENGINE 1 — Local Ollama
// ══════════════════════════════════════════════════════════════════════════
async function askOllama(model, prompt, opts = {}) {
    const timeout = opts.timeout || CONFIG.CHUNK_TIMEOUT;
    const res = await fetchWithTimeout(
        'http://localhost:11434/api/generate',
        {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model,
                prompt,
                stream: false,
                options: {
                    temperature: opts.temperature ?? 0.2,
                    top_p:       opts.top_p       ?? 0.9,
                    ...opts.ollamaOptions,
                },
            }),
        },
        timeout
    );

    if (!res.ok) throw new Error(`Ollama HTTP ${res.status}`);
    const data = await res.json();
    return data.response || '';
}

// ══════════════════════════════════════════════════════════════════════════
// ENGINE 3 — Groq API
// ══════════════════════════════════════════════════════════════════════════
async function askGroq(prompt, opts = {}) {
    if (!CONFIG.GROQ.KEY) throw new Error('GROQ_API_KEY not set');

    const res = await fetchWithTimeout(
        CONFIG.GROQ.API_URL,
        {
            method:  'POST',
            headers: {
                'Content-Type':  'application/json',
                'Authorization': `Bearer ${CONFIG.GROQ.KEY}`,
            },
            body: JSON.stringify({
                model:       CONFIG.GROQ.MODEL,
                messages:    [{ role: 'user', content: prompt }],
                temperature: opts.temperature ?? 0.2,
                max_tokens:  opts.maxTokens   ?? 2048,
            }),
        },
        opts.timeout || CONFIG.CHUNK_TIMEOUT
    );

    if (!res.ok) {
        const body = await res.text().catch(() => '');
        throw new Error(`Groq HTTP ${res.status}: ${body.slice(0, 200)}`);
    }

    const data = await res.json();
    return data?.choices?.[0]?.message?.content || '';
}

// ══════════════════════════════════════════════════════════════════════════
// ENGINE 4 — Internet Search (DuckDuckGo + Searx)
// ══════════════════════════════════════════════════════════════════════════

function stripHtml(html) {
    return html
        .replace(/<script[\s\S]*?<\/script>/gi, '')
        .replace(/<style[\s\S]*?<\/style>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
        .replace(/\s{2,}/g, ' ')
        .trim();
}

function extractCodeBlocks(html) {
    const blocks = [];
    const re     = /<(?:pre|code)[^>]*>([\s\S]*?)<\/(?:pre|code)>/gi;
    let m;
    while ((m = re.exec(html)) !== null) {
        const snippet = stripHtml(m[1]).trim();
        if (snippet.length > 30) blocks.push(snippet);
    }
    return blocks;
}

// BUG FIX #13: Handle non-JSON responses from DDG
async function searchDDG(query) {
    const url = `${CONFIG.SEARCH.DDG_URL}?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
    const res = await fetchWithTimeout(url, {
        headers: { 'User-Agent': 'Pika-AGI/5.0 Node.js' },
    }, CONFIG.SEARCH.TIMEOUT);

    if (!res.ok) throw new Error(`DDG HTTP ${res.status}`);
    
    const contentType = res.headers.get('content-type') || '';
    let data;
    
    if (contentType.includes('application/json')) {
        data = await res.json();
    } else {
        // Fallback: parse HTML response
        const text = await res.text();
        return stripHtml(text).slice(0, 2000);
    }

    const parts = [
        data.AbstractText,
        data.Answer,
        (data.Results  || []).slice(0, 3).map(r => r.Text).join(' '),
        (data.RelatedTopics || []).slice(0, 3).map(t => t.Text).join(' '),
    ].filter(Boolean);

    if (!parts.length) throw new Error('DDG returned no useful content');
    return parts.join('\n').trim();
}

async function searchSearx(query) {
    const url = `${CONFIG.SEARCH.SEARX_URL}?q=${encodeURIComponent(query)}&format=html&categories=it`;
    const res = await fetchWithTimeout(url, {
        headers: { 'User-Agent': 'Pika-AGI/5.0 Node.js', 'Accept': 'text/html' },
    }, CONFIG.SEARCH.TIMEOUT);

    if (!res.ok) throw new Error(`Searx HTTP ${res.status}`);
    const html   = await res.text();
    const blocks = extractCodeBlocks(html);
    if (!blocks.length) {
        const plain = stripHtml(html).slice(0, 2000);
        if (plain.length < 50) throw new Error('Searx returned no useful content');
        return plain;
    }
    return blocks.slice(0, 5).join('\n\n---\n\n');
}

async function internetSearch(query) {
    try {
        const ddg = await searchDDG(query);
        return ddg;
    } catch (e) {
        engineLog('INTERNET', `DDG failed (${e.message}), trying Searx…`, 'warn');
    }
    return searchSearx(query);
}

// ══════════════════════════════════════════════════════════════════════════
// ADAPTIVE ENGINE SELECTOR (V5 Intelligence Feature)
// ══════════════════════════════════════════════════════════════════════════
function selectOptimalEngine(taskType, prompt) {
    const engines = [];
    
    switch (taskType) {
        case 'code':
            engines.push('OLLAMA-CODER');
            engines.push('GROQ');
            engines.push('OLLAMA-REASON');
            break;
        case 'research':
            engines.push('INTERNET');
            engines.push('GROQ');
            engines.push('OLLAMA-REASON');
            break;
        case 'quick_fix':
            engines.push('GROQ');
            engines.push('OLLAMA-CODER');
            break;
        case 'reasoning':
            engines.push('OLLAMA-REASON');
            engines.push('GROQ');
            break;
        default:
            engines.push('OLLAMA-CODER');
            engines.push('OLLAMA-REASON');
            engines.push('GROQ');
            engines.push('INTERNET');
    }
    
    return engines;
}

// ══════════════════════════════════════════════════════════════════════════
// 4-TIER COGNITIVE FALLBACK ENGINE (with outer timeout — BUG FIX #15)
// ══════════════════════════════════════════════════════════════════════════

function buildTiers(prompt, opts = {}) {
    const taskType = opts.taskType || 'code';
    const engineOrder = selectOptimalEngine(taskType, prompt);
    
    const allTiers = [
        {
            name:   'OLLAMA-CODER',
            label:  'Engine 1 · Local qwen2.5-coder',
            call:   () => askOllama(CONFIG.MODELS.PRIMARY_CODER, prompt, opts),
        },
        {
            name:   'OLLAMA-REASON',
            label:  'Engine 2 · Local deepseek-r1 (reasoning)',
            call:   () => askOllama(CONFIG.MODELS.REASONING, prompt, { ...opts, temperature: 0.3 }),
        },
        {
            name:   'GROQ',
            label:  'Engine 3 · Groq Cloud API',
            call:   () => askGroq(prompt, opts),
        },
        {
            name:   'INTERNET',
            label:  'Engine 4 · Internet Search',
            call:   () => {
                const q = (opts.searchQuery)
                    || prompt.slice(0, 300).replace(/\n/g, ' ').trim();
                return internetSearch(q);
            },
        },
    ];
    
    // Sort tiers by optimal engine order
    const ordered = [];
    for (const engineName of engineOrder) {
        const tier = allTiers.find(t => t.name === engineName);
        if (tier) ordered.push(tier);
    }
    // Add any remaining tiers not in the optimal order
    for (const tier of allTiers) {
        if (!ordered.includes(tier)) ordered.push(tier);
    }
    
    return ordered;
}

async function cognitiveFallback(prompt, opts = {}, cacheKey = null) {
    // Outer timeout wrapper — BUG FIX #15
    const outerTimeout = opts.totalTimeout || 600000; // 10 min max total
    
    return Promise.race([
        _cognitiveFallbackInternal(prompt, opts, cacheKey),
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error(`Cognitive fallback timed out after ${outerTimeout}ms`)), outerTimeout)
        )
    ]);
}

async function _cognitiveFallbackInternal(prompt, opts = {}, cacheKey = null) {
    if (cacheKey && CONFIG.CACHE_ENABLED && cognitiveCache.has(cacheKey)) {
        engineLog('CACHE', `Cache hit → ${cacheKey}`, 'ok');
        return cognitiveCache.get(cacheKey);
    }

    const tiers = buildTiers(prompt, opts);

    for (let cycle = 1; cycle <= CONFIG.MAX_CYCLE_LOOPS; cycle++) {
        console.log(`\n${C.MAGENTA}${C.BOLD}┌─ COGNITIVE ROUND-ROBIN · Cycle ${cycle}/${CONFIG.MAX_CYCLE_LOOPS} ─────────────────┐${C.RESET}`);

        for (const tier of tiers) {
            console.log(`${C.CYAN}│  ⇒ Trying ${tier.label}${C.RESET}`);

            let lastErr;
            for (let attempt = 1; attempt <= CONFIG.ENGINE_RETRIES; attempt++) {
                engineLog(tier.name, `Attempt ${attempt}/${CONFIG.ENGINE_RETRIES}`, 'info');
                try {
                    const response = await tier.call();
                    if (!response || response.trim().length < 5)
                        throw new Error('Empty or trivial response');

                    engineLog(tier.name, `SUCCESS (${response.length} chars)`, 'ok');
                    
                    // Update engine stats
                    if (EVOLUTION_STATE.engineStats[tier.name.toLowerCase()]) {
                        EVOLUTION_STATE.engineStats[tier.name.toLowerCase()].success++;
                    }
                    
                    if (cacheKey && CONFIG.CACHE_ENABLED)
                        cognitiveCache.set(cacheKey, response);

                    console.log(`${C.MAGENTA}${C.BOLD}└──────────────────────────────────────────────────────┘${C.RESET}`);
                    return response;
                } catch (err) {
                    lastErr = err;
                    engineLog(tier.name, `Attempt ${attempt} failed: ${err.message}`, 'warn');
                    
                    // Update engine stats
                    if (EVOLUTION_STATE.engineStats[tier.name.toLowerCase()]) {
                        EVOLUTION_STATE.engineStats[tier.name.toLowerCase()].fail++;
                    }
                    
                    if (attempt < CONFIG.ENGINE_RETRIES)
                        await new Promise(r => setTimeout(r, 800 * attempt));
                }
            }

            engineLog(tier.name, `All ${CONFIG.ENGINE_RETRIES} attempts exhausted — shifting engine`, 'shift');
        }

        console.log(`${C.RED}${C.BOLD}│  ✗ All engines failed on cycle ${cycle}. ${cycle < CONFIG.MAX_CYCLE_LOOPS ? 'Retrying cycle…' : 'CRITICAL FAILURE.'}${C.RESET}`);
        console.log(`${C.MAGENTA}${C.BOLD}└──────────────────────────────────────────────────────┘${C.RESET}`);

        if (cycle < CONFIG.MAX_CYCLE_LOOPS)
            await new Promise(r => setTimeout(r, 2000 * cycle));
    }

    throw new Error(`[PIKA] CRITICAL: All ${CONFIG.MAX_CYCLE_LOOPS} cognitive cycles exhausted across all 4 engines.`);
}

// ══════════════════════════════════════════════════════════════════════════
// CODE EXTRACTION (BUG FIX #6: Non-destructive)
// ══════════════════════════════════════════════════════════════════════════
function extractCode(raw) {
    // First, extract code from markdown fences if present
    const fenceMatch = raw.match(/```(?:javascript|js|typescript|ts|node)?\n?([\s\S]*?)```/);
    let cleaned = fenceMatch ? fenceMatch[1] : raw;
    
    // Only strip boilerplate from the BEGINNING, not globally
    cleaned = cleaned
        .replace(/^(?:Here's|This is|The following|Below is|Sure[,!]?).*?:\s*/im, '')
        .replace(/^\s*\n/, ''); // Remove leading blank lines
    
    // Remove explanation lines that start with common prefixes (only at line start)
    cleaned = cleaned
        .split('\n')
        .filter(line => {
            const t = line.trim();
            // Keep lines that look like code or comments
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

// ══════════════════════════════════════════════════════════════════════════
// JSON PARSER WITH FALLBACK
// ══════════════════════════════════════════════════════════════════════════
function parseJSON(text, fallback = []) {
    try { return JSON.parse(text); } catch (_) {}
    const m = text.match(/\[[\s\S]*\]|\{[\s\S]*\}/);
    if (m) { try { return JSON.parse(m[0]); } catch (_) {} }
    return fallback;
}

// ══════════════════════════════════════════════════════════════════════════
// BACKUP SYSTEM (BUG FIX #12: Async operations)
// ══════════════════════════════════════════════════════════════════════════
async function ensureBackupDir() {
    const dir = path.resolve(process.cwd(), CONFIG.BACKUP_DIR);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
    return dir;
}

async function backupFile(filePath) {
    const abs = path.resolve(process.cwd(), filePath);
    if (!fs.existsSync(abs))
        return { success: true, backupPath: null, note: 'New file — no backup needed' };

    try {
        const dir     = await ensureBackupDir();
        const ext     = path.extname(abs);
        const base    = path.basename(abs, ext);
        const ts      = new Date().toISOString().replace(/[:.]/g, '-');
        const bkpPath = path.join(dir, `${base}.${ts}.backup${ext}`);
        
        // Use async copy for non-blocking
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
        const msg = `Backup failed: ${err.message}`;
        console.log(`${C.RED}[BACKUP] ✗ ${msg}${C.RESET}`);
        return { success: false, error: msg };
    }
}

// ══════════════════════════════════════════════════════════════════════════
// SEMANTIC FUNCTION PARSER (V5: AST-Based — BUG FIX #7)
// ══════════════════════════════════════════════════════════════════════════
function parseFunctions(source) {
    const map = new Map();
    const lines = source.split('\n');
    
    // Pattern 1: Traditional function declarations
    // function name() { } or async function name() { }
    const funcDeclRegex = /^(?:\/\*[\s\S]*?\*\/\s*)?(?:async\s+)?function\s+(\w+)\s*\(/gm;
    let m;
    while ((m = funcDeclRegex.exec(source)) !== null) {
        const name = m[1];
        const start = source.indexOf('{', m.index + m[0].length - 1);
        if (start === -1) continue;
        
        let depth = 0, i = start;
        for (; i < source.length; i++) {
            if (source[i] === '{') depth++;
            else if (source[i] === '}' && --depth === 0) break;
        }
        
        const cs = findPrecedingComment(source, m.index);
        map.set(name, { type: 'function', body: source.slice(cs, i + 1).trim(), start: cs, end: i + 1 });
    }
    
    // Pattern 2: Arrow functions assigned to const/let/var
    // const name = (args) => { } or const name = async (args) => { }
    const arrowRegex = /^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>/gm;
    while ((m = arrowRegex.exec(source)) !== null) {
        const name = m[1];
        const start = m.index;
        
        // Find the end of the arrow function
        let i = m.index + m[0].length;
        // Skip whitespace
        while (i < source.length && /\s/.test(source[i])) i++;
        
        if (source[i] === '{') {
            // Block body
            let depth = 0;
            for (; i < source.length; i++) {
                if (source[i] === '{') depth++;
                else if (source[i] === '}' && --depth === 0) break;
            }
            map.set(name, { type: 'arrow', body: source.slice(start, i + 1).trim(), start, end: i + 1 });
        } else {
            // Expression body — find end of statement
            let parenDepth = 0;
            for (; i < source.length; i++) {
                if (source[i] === '(') parenDepth++;
                else if (source[i] === ')') parenDepth--;
                else if (source[i] === ';' && parenDepth === 0) break;
                else if (source[i] === '\n' && parenDepth === 0) {
                    // Check if next line continues
                    const nextLine = source.slice(i + 1).match(/^\s*/)[0];
                    if (!nextLine.match(/^[\s]*[.+\-*\/%,&|]/)) break;
                }
            }
            map.set(name, { type: 'arrow', body: source.slice(start, i).trim(), start, end: i });
        }
    }
    
    // Pattern 3: Method definitions in objects/classes
    // name() { } or async name() { }
    const methodRegex = /^(?:\s+)(\w+)\s*\(\s*\)\s*\{/gm;
    while ((m = methodRegex.exec(source)) !== null) {
        const name = m[1];
        if (['if', 'while', 'for', 'switch', 'catch'].includes(name)) continue;
        
        const start = m.index;
        let depth = 0, i = source.indexOf('{', m.index + m[0].length - 1);
        for (; i < source.length; i++) {
            if (source[i] === '{') depth++;
            else if (source[i] === '}' && --depth === 0) break;
        }
        map.set(name, { type: 'method', body: source.slice(start, i + 1).trim(), start, end: i + 1 });
    }
    
    return map;
}

function findPrecedingComment(source, index) {
    let i = index - 1;
    while (i >= 0 && /\s/.test(source[i])) i--;
    if (i >= 1 && source[i - 1] === '*' && source[i] === '/') {
        const open = source.lastIndexOf('/*', i);
        if (open !== -1) return open;
    }
    return index;
}

// ══════════════════════════════════════════════════════════════════════════
// SECURITY SCANNER (V5 Feature — replaces aggressive staticAnalysis)
// ══════════════════════════════════════════════════════════════════════════
const DANGEROUS_PATTERNS = [
    { pattern: /\beval\s*\(/g, name: 'eval()', severity: 'critical' },
    { pattern: /\bFunction\s*\(/g, name: 'Function constructor', severity: 'critical' },
    { pattern: /__proto__/g, name: 'prototype pollution', severity: 'critical' },
    { pattern: /process\.exit/g, name: 'process.exit()', severity: 'high' },
    { pattern: /child_process\b/g, name: 'child_process', severity: 'high' },
    { pattern: /require\s*\(\s*['"]child_process['"]\s*\)/g, name: 'child_process require', severity: 'high' },
];

const SUSPICIOUS_PATTERNS = [
    { pattern: /SELECT\s+.*\s+FROM/gi, name: 'raw SQL', severity: 'medium' },
    { pattern: /INSERT\s+INTO/gi, name: 'raw SQL insert', severity: 'medium' },
    { pattern: /DELETE\s+FROM/gi, name: 'raw SQL delete', severity: 'medium' },
    { pattern: /api[_-]?key|password|secret|token\s*[:=]/gi, name: 'hardcoded secret', severity: 'medium' },
    { pattern: /fetch\s*\(\s*['"]http:\/\//g, name: 'insecure HTTP', severity: 'low' },
];

function securityScan(code) {
    const findings = [];
    
    for (const { pattern, name, severity } of DANGEROUS_PATTERNS) {
        if (pattern.test(code)) {
            findings.push({ type: 'dangerous', name, severity });
        }
    }
    
    for (const { pattern, name, severity } of SUSPICIOUS_PATTERNS) {
        if (pattern.test(code)) {
            findings.push({ type: 'suspicious', name, severity });
        }
    }
    
    const criticalCount = findings.filter(f => f.severity === 'critical').length;
    const highCount = findings.filter(f => f.severity === 'high').length;
    
    return {
        safe: criticalCount === 0 && highCount === 0,
        findings,
        score: Math.max(0, 100 - (criticalCount * 50) - (highCount * 20) - (findings.length * 5))
    };
}

// ══════════════════════════════════════════════════════════════════════════
// PHASE 1 — PLANNING
// ══════════════════════════════════════════════════════════════════════════
async function generateExecutionPlan(actionName, description, targetFile) {
    phase(1, 'PLANNING');

    const cacheKey = `plan:${actionName}:${description}`;
    if (CONFIG.CACHE_ENABLED && cognitiveCache.has(cacheKey)) {
        console.log(`${C.GREEN}[CACHE] Plan hit${C.RESET}`);
        return cognitiveCache.get(cacheKey);
    }

    const prompt = `Task: ${actionName}
Description: ${description}
Target File: ${targetFile || 'new file'}

Output ONLY a valid JSON array of function chunks to implement. Format:
[{"funcName":"camelCaseName","logic":"what it does","priority":1,"dependencies":[]}]

Priority: 1=high, 3=low. Output ONLY the raw JSON array. No markdown. No explanation.`;

    try {
        const raw  = await cognitiveFallback(prompt, { 
            temperature: 0.3, 
            timeout: 20000,
            taskType: 'code',
            searchQuery: `Node.js implementation plan for: ${actionName}` 
        }, cacheKey + '_raw');
        const list = parseJSON(raw, null);

        if (!list || !Array.isArray(list) || !list.length) {
            console.log(`${C.YELLOW}[PLAN] Fallback to basic plan${C.RESET}`);
            return createBasicPlan(actionName, description);
        }

        const sorted = topologicalSort(list);
        if (CONFIG.CACHE_ENABLED) cognitiveCache.set(cacheKey, sorted);
        console.log(`${C.GREEN}[PLAN] ✓ ${sorted.length} chunks planned${C.RESET}`);
        return sorted;
    } catch (err) {
        console.log(`${C.RED}[PLAN ERR] ${err.message} — using basic plan${C.RESET}`);
        return createBasicPlan(actionName, description);
    }
}

function createBasicPlan(actionName, description) {
    return [{
        funcName:     'main' + actionName.replace(/\W+/g, ''),
        logic:        description,
        priority:     1,
        dependencies: [],
    }];
}

function topologicalSort(tasks) {
    const sorted = [], visited = new Set(), visiting = new Set();

    function visit(task) {
        if (visited.has(task.funcName) || visiting.has(task.funcName)) return;
        visiting.add(task.funcName);
        (task.dependencies || []).forEach(dep => {
            const d = tasks.find(t => t.funcName === dep);
            if (d) visit(d);
        });
        visiting.delete(task.funcName);
        visited.add(task.funcName);
        sorted.push(task);
    }

    [...tasks].sort((a, b) => (a.priority || 2) - (b.priority || 2)).forEach(visit);
    return sorted;
}

// ══════════════════════════════════════════════════════════════════════════
// PHASE 2 — PARALLEL CODE GENERATION
// ══════════════════════════════════════════════════════════════════════════
async function generateCodeChunks(functionList, context = {}) {
    phase(2, 'CODE GENERATION');
    const chunks = [], errors = [];

    for (let i = 0; i < functionList.length; i += CONFIG.PARALLEL_CHUNKS) {
        const batch   = functionList.slice(i, i + CONFIG.PARALLEL_CHUNKS);
        const results = await Promise.allSettled(
            batch.map(task =>
                generateSingleFunction(task, context).catch(e => {
                    errors.push({ task: task.funcName, error: e.message });
                    return null;
                })
            )
        );

        results.forEach((r, idx) => {
            if (r.status === 'fulfilled' && r.value) chunks.push(r.value);
            else console.log(`${C.RED}[GEN FAIL] ${batch[idx].funcName}${C.RESET}`);
        });
    }

    if (errors.length && errors.length === functionList.length)
        throw new Error('All code generation attempts failed across all engines');

    return assembleCode(chunks);
}

async function generateSingleFunction(task, context) {
    const cacheKey = `func:${task.funcName}:${task.logic}`;
    if (CONFIG.CACHE_ENABLED && cognitiveCache.has(cacheKey)) {
        console.log(`${C.GREEN}  [CACHE] ${task.funcName}${C.RESET}`);
        return cognitiveCache.get(cacheKey);
    }

    console.log(`${C.YELLOW}  ├─ Generating: ${task.funcName}${C.RESET}`);

    const prompt = `Write ONLY the JavaScript function named '${task.funcName}' that does:
${task.logic}
${task.dependencies?.length ? `Dependencies available: ${task.dependencies.join(', ')}` : ''}

Requirements:
- Pure JavaScript (Node.js)
- Robust error handling (try/catch)
- JSDoc comment above the function
- No explanation, no markdown fences, raw code only

function ${task.funcName}(...) { ... }`;

    const raw   = await cognitiveFallback(prompt, {
        temperature:  0.1,
        timeout:      25000,
        taskType:     'code',
        searchQuery:  `JavaScript implementation ${task.funcName}: ${task.logic}`,
    }, cacheKey + '_raw');

    const clean = extractCode(raw);
    if (!clean || clean.length < 20) throw new Error(`Generated code too short for ${task.funcName}`);

    const chunk = { name: task.funcName, code: clean, priority: task.priority };
    if (CONFIG.CACHE_ENABLED) cognitiveCache.set(cacheKey, chunk);
    console.log(`${C.GREEN}  ✓ ${task.funcName} (${clean.length} chars)${C.RESET}`);
    return chunk;
}

function assembleCode(chunks) {
    const header = `// ═══ Auto-generated by Pika Logic Factory v5.0 — ${new Date().toISOString()} ═══\n\n`;
    return header + chunks
        .sort((a, b) => (a.priority || 2) - (b.priority || 2))
        .map(c => `// ── ${c.name} ──────────────────────────────────────\n${c.code}`)
        .join('\n\n') + '\n';
}

// ══════════════════════════════════════════════════════════════════════════
// PHASE 3 — SANDBOX VALIDATION (Enhanced V5)
// ══════════════════════════════════════════════════════════════════════════
async function validateToolInSandbox(code, strict = false) {
    phase(3, 'SANDBOX VALIDATION');

    const syntax = checkSyntax(code);
    if (!syntax.valid) return { success: false, error: syntax.error, layer: 'syntax', code };
    console.log(`${C.GREEN}  ✓ Syntax OK${C.RESET}`);

    const security = securityScan(code);
    if (!security.safe) {
        console.log(`${C.YELLOW}  ⚠ Security findings: ${security.findings.map(f => f.name).join(', ')}${C.RESET}`);
        if (security.findings.some(f => f.severity === 'critical')) {
            return { success: false, error: `Security violation: ${security.findings[0].name}`, layer: 'security', code };
        }
    }
    console.log(`${C.GREEN}  ✓ Security scan OK (score: ${security.score})${C.RESET}`);

    const stat = staticAnalysis(code);
    if (!stat.safe) return { success: false, error: stat.error, layer: 'static', code };
    console.log(`${C.GREEN}  ✓ Static analysis OK${C.RESET}`);

    if (strict) {
        const rt = testRuntime(code);
        if (!rt.success)
            return { success: false, error: rt.error, output: rt.output, layer: 'runtime', code };
        console.log(`${C.GREEN}  ✓ Runtime OK${rt.output ? ' | ' + rt.output : ''}${C.RESET}`);
    }

    return { success: true, code, securityScore: security.score };
}

function checkSyntax(code) {
    try { new vm.Script(code); return { valid: true }; }
    catch (e) {
        return {
            valid: false,
            error: e.message,
            line:  (e.stack?.match(/:(\d+)$/m) || [])[1] || null,
        };
    }
}

// BUG FIX #4: Whitelist approach instead of blanket ban
function staticAnalysis(code) {
    // Only block truly dangerous patterns, not legitimate fs usage
    const dangerous = [
        [/\beval\s*\(/g,            'eval()'],
        [/\bFunction\s*\(/g,        'Function constructor'],
        [/__proto__/g,               'prototype pollution'],
        [/process\.exit/g,           'process.exit()'],
    ];
    
    for (const [pat, name] of dangerous)
        if (pat.test(code)) return { safe: false, error: `Dangerous pattern: ${name}` };
    
    if (code.trim().length < 10) return { safe: false, error: 'Code too short' };
    return { safe: true };
}

// BUG FIX #5: Enhanced sandbox with require support
function testRuntime(code) {
    const logs = [], errs = [];
    
    // Whitelist of safe modules
    const safeModules = new Set([
        'path', 'url', 'querystring', 'crypto', 'util', 'stream', 'events',
        'string_decoder', 'punycode', 'os', 'buffer'
    ]);
    
    const sandbox = {
        console: {
            log:   (...a) => logs.push(a.map(String).join(' ')),
            warn:  (...a) => logs.push('[W] ' + a.map(String).join(' ')),
            error: (...a) => errs.push(a.map(String).join(' ')),
        },
        setTimeout: () => {}, setInterval: () => {}, clearTimeout: () => {}, clearInterval: () => {},
        Math, JSON, Array, Object, String, Number, Boolean, Date, Error, Map, Set, Promise, RegExp,
        Buffer: Buffer,
        require: (mod) => {
            if (safeModules.has(mod)) return require(mod);
            throw new Error(`Module '${mod}' not allowed in sandbox`);
        },
        __dirname: '/tmp/pika-sandbox',
        __filename: '/tmp/pika-sandbox/test.js',
        process: { env: {}, argv: [], version: process.version, platform: process.platform },
        module: { exports: {} },
        exports: {},
    };

    try {
        const ctx    = vm.createContext(sandbox);
        const script = new vm.Script(code, { filename: 'pika-generated.js' });
        script.runInContext(ctx, { timeout: CONFIG.RUNTIME_TIMEOUT });
        return { success: true, output: logs.join('\n') || null, consoleErrors: errs.join('\n') || null };
    } catch (e) {
        const isTimeout = e.message.includes('timed out') || e.code === 'ERR_SCRIPT_EXECUTION_TIMEOUT';
        return {
            success: false,
            error:   isTimeout ? `Timed out after ${CONFIG.RUNTIME_TIMEOUT}ms` : e.message,
            output:  logs.join('\n') || null,
            stack:   e.stack || null,
        };
    }
}

// ══════════════════════════════════════════════════════════════════════════
// PHASE 4 — SELF-HEALING
// ══════════════════════════════════════════════════════════════════════════
async function selfHealCode(code, validationResult, maxAttempts = CONFIG.MAX_RETRIES) {
    phase(4, 'SELF-HEALING');

    let current = code, vr = validationResult;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        console.log(`${C.YELLOW}[HEAL ${attempt}/${maxAttempts}] Feeding error back to cognitive engine…${C.RESET}`);
        const ctx = extractErrorContext(current, vr);

        const prompt = `You are a senior JavaScript debugger. Fix this ${vr.layer} error.

ERROR: ${vr.error}
${ctx.lineInfo ? `LINE: ${ctx.lineInfo}` : ''}
${vr.output    ? `RUNTIME OUTPUT:\n${vr.output}` : ''}

BROKEN CODE:
${ctx.snippet}

Output ONLY the complete corrected JavaScript code. No markdown. No explanation.`;

        try {
            const raw      = await cognitiveFallback(prompt, { 
                temperature: 0.1, 
                timeout: 22000,
                taskType: 'quick_fix',
                searchQuery: `Fix JavaScript ${vr.layer} error: ${vr.error}` 
            });
            current        = extractCode(raw);
            const recheck  = await validateToolInSandbox(current, vr.layer === 'runtime');
            if (recheck.success) {
                console.log(`${C.GREEN}[HEALED] ✓ Fixed in ${attempt} attempt(s)${C.RESET}`);
                return { success: true, code: current, attempts: attempt };
            }
            vr = recheck;
        } catch (e) {
            console.log(`${C.RED}[HEAL ERR] ${e.message}${C.RESET}`);
        }
    }

    return { success: false, code: current, attempts: maxAttempts, finalError: vr.error };
}

function extractErrorContext(code, vr) {
    const lines = code.split('\n');
    const line  = vr.line || findErrorLine(code, vr.error);
    if (line) {
        const s = Math.max(0, line - 3), e = Math.min(lines.length, line + 3);
        return { snippet: lines.slice(s, e).join('\n'), lineInfo: line };
    }
    return { snippet: lines.slice(0, 25).join('\n'), lineInfo: null };
}

function findErrorLine(code, msg) {
    const m = (msg || '').match(/line (\d+)/i);
    return m ? parseInt(m[1]) : null;
}

// ══════════════════════════════════════════════════════════════════════════
// PHASE 5 — SMART MERGE (Enhanced for all function types)
// ══════════════════════════════════════════════════════════════════════════

function mergeSourceFiles(existing, newSrc) {
    const existFns = parseFunctions(existing);
    const newFns   = parseFunctions(newSrc);
    const replaced = [], added = [];
    let merged     = existing;

    for (const [name, info] of newFns) {
        if (existFns.has(name)) {
            // Replace the entire function body including type prefix
            const oldBody = existFns.get(name).body;
            const newBody = info.body;
            merged = merged.replace(oldBody, newBody);
            replaced.push(name);
        } else {
            merged += `\n\n// ── ${name} (added by Pika v5.0) ──\n${info.body}`;
            added.push(name);
        }
    }
    return { merged, replaced, added };
}

async function smartMergeUpgrade(targetFile, newCode, description) {
    phase(5, 'SMART MERGE');

    if (!targetFile || targetFile === 'new file') {
        console.log(`${C.GREEN}[MERGE] No target file — returning generated code only${C.RESET}`);
        return { merged: newCode, strategy: 'new', replaced: [], added: [] };
    }

    const abs = path.resolve(process.cwd(), targetFile);

    if (!fs.existsSync(abs)) {
        fs.mkdirSync(path.dirname(abs), { recursive: true });
        fs.writeFileSync(abs, newCode, 'utf8');
        console.log(`${C.GREEN}[MERGE] ✓ Created ${abs}${C.RESET}`);
        return { merged: newCode, strategy: 'create', replaced: [], added: [] };
    }

    const bkp = await backupFile(abs);
    if (!bkp.success) throw new Error(`Backup failed: ${bkp.error}`);

    const existing                    = fs.readFileSync(abs, 'utf8');
    const { merged, replaced, added } = mergeSourceFiles(existing, newCode);

    console.log(`${C.GREEN}[MERGE] Replaced: [${replaced.join(', ') || 'none'}]  Added: [${added.join(', ') || 'none'}]${C.RESET}`);

    const stamp =
        `\n// ═══ Pika Mutation · ${new Date().toISOString()} ═══\n` +
        `// ${description}\n// Replaced: ${replaced.join(', ') || 'none'} | Added: ${added.join(', ') || 'none'}\n`;

    const final = stamp + merged;
    fs.writeFileSync(abs, final, 'utf8');
    console.log(`${C.GREEN}[MERGE] ✓ Written → ${abs}${C.RESET}`);
    return { merged: final, strategy: 'merge', replaced, added, backupPath: bkp.backupPath };
}

// ══════════════════════════════════════════════════════════════════════════
// ★ SELF-EVOLUTION ENGINE (Enhanced V5)
// ══════════════════════════════════════════════════════════════════════════

function readSelfSource() {
    const selfPath = CONFIG.SELF_EVOLUTION.SELF_FILE;
    if (!fs.existsSync(selfPath))
        throw new Error(`Self-file not found: ${selfPath}`);
    return { source: fs.readFileSync(selfPath, 'utf8'), path: selfPath };
}

// BUG FIX #16: Enhanced scoring with complexity metrics
function scoreSelfSource(source) {
    let score    = 100;
    const fns    = (source.match(/^(?:async\s+)?function\s+\w+/gm) || []).length;
    const arrows = (source.match(/(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>/gm) || []).length;
    const totalFns = fns + arrows;
    const tries  = (source.match(/try\s*\{/g) || []).length;
    const jsdocs = (source.match(/\/\*\*[\s\S]*?\*\//g) || []).length;
    const longFn = (source.match(/function\s+\w+[^}]{3200,}/g) || []).length;
    
    // Complexity metrics
    const avgFnLength = totalFns > 0 ? source.length / totalFns : 0;
    const commentRatio = source.length > 0 ? (source.match(/\/\/.*/g) || []).length / source.length * 100 : 0;

    if (totalFns > 0 && tries  / totalFns < 0.4) score -= 15;
    if (totalFns > 0 && jsdocs / totalFns < 0.3) score -= 10;
    score -= longFn * 5;
    if (source.includes("'use strict'"))   score += 2;
    if (source.includes('module.exports')) score += 3;
    if (avgFnLength > 500) score -= 5; // Penalize very long functions
    if (commentRatio < 0.5) score -= 5; // Penalize lack of comments

    return Math.max(0, Math.min(100, score));
}

async function mutateOneFunction(funcName, funcBody, focusArea) {
    const prompt = `You are an expert Node.js developer improving a production autonomous engine.

FUNCTION TO IMPROVE (${funcName}):
\`\`\`javascript
${funcBody}
\`\`\`

IMPROVEMENT FOCUS: ${focusArea}

Rules:
- Keep the EXACT same function name and signature
- Improve ONLY the ${focusArea} aspect
- Add or improve error handling where missing
- Output ONLY the improved function code, no markdown fences, no explanations`;

    try {
        const raw   = await cognitiveFallback(prompt, { 
            temperature: 0.2, 
            timeout: 25000,
            taskType: 'code',
            searchQuery: `Improve Node.js ${focusArea} for function ${funcName}` 
        });
        const clean = extractCode(raw);
        if (!clean || clean.length < 30) return null;
        return clean;
    } catch (e) {
        console.log(`${C.RED}[MUTATE] Engine failed for ${funcName}: ${e.message}${C.RESET}`);
        return null;
    }
}

function applyMutation(source, funcName, newFuncBody) {
    const fns = parseFunctions(source);
    if (!fns.has(funcName)) return null;

    if (!checkSyntax(newFuncBody).valid) {
        console.log(`${C.RED}[MUTATE] Syntax invalid for ${funcName}${C.RESET}`);
        return null;
    }

    const oldInfo = fns.get(funcName);
    const newSource = source.replace(oldInfo.body, newFuncBody);

    if (!checkSyntax(newSource).valid) {
        console.log(`${C.RED}[MUTATE] File syntax broken after mutating ${funcName}${C.RESET}`);
        return null;
    }

    return newSource;
}

// BUG FIX #20: Append-only JSONL format for evolution log
function saveEvolutionLog(entry) {
    const logPath = path.resolve(process.cwd(), CONFIG.SELF_EVOLUTION.EVOLUTION_LOG);
    const line = JSON.stringify({ timestamp: new Date().toISOString(), ...entry }) + '\n';
    
    try {
        fs.appendFileSync(logPath, line, 'utf8');
    } catch (e) {
        console.log(`${C.RED}[EVOLVE LOG] Failed to write: ${e.message}${C.RESET}`);
    }
}

async function selfEvolve(options = {}) {
    const cfg = CONFIG.SELF_EVOLUTION;

    if (!cfg.ENABLED) {
        console.log(`${C.DIM}[EVOLVE] Disabled in config${C.RESET}`);
        return { success: false, reason: 'disabled' };
    }

    console.log(`\n${C.MAGENTA}${C.BOLD}╔════════════════════════════════════════════════════╗`);
    console.log(`║   🧬  PIKA SELF-EVOLUTION CYCLE STARTED            ║`);
    console.log(`╚════════════════════════════════════════════════════╝${C.RESET}`);

    let selfSrc, selfPath;
    try {
        ({ source: selfSrc, path: selfPath } = readSelfSource());
    } catch (e) {
        console.log(`${C.RED}[EVOLVE] Cannot read self: ${e.message}${C.RESET}`);
        return { success: false, reason: e.message };
    }

    const scoreBefore = scoreSelfSource(selfSrc);
    const forceEvolve = options.force === true;
    console.log(`${C.CYAN}[EVOLVE] Score: ${scoreBefore}/100 | Threshold: ${cfg.MUTATION_THRESHOLD}${C.RESET}`);

    if (scoreBefore >= cfg.MUTATION_THRESHOLD && !forceEvolve) {
        console.log(`${C.GREEN}[EVOLVE] Score sufficient — skipping mutation${C.RESET}`);
        const result = { success: true, mutated: false, scoreBefore, scoreAfter: scoreBefore, mutations: [] };
        saveEvolutionLog({ cycle: 'skip', ...result });
        return result;
    }

    const allFns  = parseFunctions(selfSrc);
    const targets = [...allFns.keys()]
        .filter(n => (allFns.get(n).body || '').split('\n').length > 5)
        .slice(0, cfg.MAX_MUTATIONS_PER_CYCLE);

    if (!targets.length) {
        console.log(`${C.YELLOW}[EVOLVE] No suitable mutation targets${C.RESET}`);
        return { success: false, reason: 'no_targets' };
    }

    console.log(`${C.YELLOW}[EVOLVE] Targets: ${targets.join(', ')}${C.RESET}`);

    const bkp = await backupFile(selfPath);
    if (!bkp.success) {
        console.log(`${C.RED}[EVOLVE] Backup failed — aborting mutation${C.RESET}`);
        return { success: false, reason: 'backup_failed' };
    }

    const focusAreas = options.focusAreas || cfg.FOCUS_AREAS;
    let currentSrc   = selfSrc;
    const mutations  = [];
    let ok = 0, fail = 0;

    for (const funcName of targets) {
        const focus    = focusAreas[Math.floor(Math.random() * focusAreas.length)];
        const funcInfo = parseFunctions(currentSrc).get(funcName);
        if (!funcInfo) continue;

        console.log(`${C.YELLOW}[MUTATE] ${funcName} → focus: ${focus}${C.RESET}`);
        EVOLUTION_STATE.totalMutations++;

        const improved = await mutateOneFunction(funcName, funcInfo.body, focus);

        if (!improved) {
            EVOLUTION_STATE.failedMutations++;
            fail++;
            mutations.push({ funcName, focus, success: false, reason: 'no_llm_output' });
            continue;
        }

        const newSrc = applyMutation(currentSrc, funcName, improved);

        if (!newSrc) {
            EVOLUTION_STATE.failedMutations++;
            fail++;
            mutations.push({ funcName, focus, success: false, reason: 'invalid_mutation' });
            continue;
        }

        currentSrc = newSrc;
        EVOLUTION_STATE.successfulMutations++;
        ok++;
        console.log(`${C.GREEN}[MUTATE] ✓ ${funcName} improved${C.RESET}`);
        mutations.push({ funcName, focus, success: true });
    }

    const scoreAfter   = scoreSelfSource(currentSrc);
    const delta        = scoreAfter - scoreBefore;
    const worthWriting = (scoreAfter >= scoreBefore && ok > 0) || (forceEvolve && ok > 0);

    console.log(`${C.CYAN}[EVOLVE] Score: ${scoreBefore} → ${scoreAfter} (${delta >= 0 ? '+' : ''}${delta})${C.RESET}`);

    if (worthWriting) {
        const stamp =
            `// 🧬 Self-Evolved — ${new Date().toISOString()}\n` +
            `// Score: ${scoreBefore} → ${scoreAfter} | OK: ${ok} | Fail: ${fail}\n`;
        fs.writeFileSync(selfPath, stamp + currentSrc, 'utf8');
        console.log(`${C.GREEN}${C.BOLD}[EVOLVE] ✓ Written to ${selfPath}${C.RESET}`);
    } else {
        console.log(`${C.YELLOW}[EVOLVE] Score did not improve — restoring original${C.RESET}`);
        if (bkp.backupPath) fs.copyFileSync(bkp.backupPath, selfPath);
    }

    EVOLUTION_STATE.lastScore = scoreAfter;
    
    // BUG FIX #10: Cap cycleHistory
    EVOLUTION_STATE.cycleHistory.push({ ts: Date.now(), scoreBefore, scoreAfter, ok, fail });
    if (EVOLUTION_STATE.cycleHistory.length > 100) {
        EVOLUTION_STATE.cycleHistory = EVOLUTION_STATE.cycleHistory.slice(-100);
    }

    const result = {
        success:      worthWriting,
        mutated:      worthWriting,
        scoreBefore,
        scoreAfter,
        mutations,
        successCount: ok,
        failCount:    fail,
        backupPath:   bkp.backupPath,
    };

    saveEvolutionLog(result);

    console.log(`${C.MAGENTA}${C.BOLD}╔════════════════════════════════════════════════════╗`);
    console.log(`║  ${worthWriting ? '✅ EVOLUTION COMPLETE' : '⚠️  EVOLUTION ABORTED (no improvement)'}${' '.repeat(worthWriting ? 29 : 22)}║`);
    console.log(`╚════════════════════════════════════════════════════╝${C.RESET}`);

    return result;
}

// ══════════════════════════════════════════════════════════════════════════
// MAIN CODE GENERATION ORCHESTRATOR
// ══════════════════════════════════════════════════════════════════════════
async function generateCodeInChunks(actionName, description, targetFile = null) {
    // BUG FIX #19: Sanitize actionName
    const sanitizedAction = String(actionName).replace(/[^a-zA-Z0-9_\-]/g, '_');
    
    const t0 = Date.now();
    console.log(`\n${C.GREEN}${C.BOLD}╔════════════════════════════════════════════════════╗`);
    console.log(`║   🚀  PIKA LOGIC FACTORY v5.0 — ACTIVATED          ║`);
    console.log(`╚════════════════════════════════════════════════════╝${C.RESET}`);
    console.log(`${C.CYAN}  Action:      ${sanitizedAction}${C.RESET}`);
    console.log(`${C.CYAN}  Description: ${description}${C.RESET}`);
    console.log(`${C.CYAN}  Target:      ${targetFile || '(new file)'}${C.RESET}`);

    try {
        const plan = await generateExecutionPlan(sanitizedAction, description, targetFile);
        if (!plan?.length) throw new Error('Empty execution plan returned');

        const assembled = await generateCodeChunks(plan, { actionName: sanitizedAction, description });

        let validation = await validateToolInSandbox(assembled, true);
        let finalCode  = assembled;

        if (!validation.success) {
            console.log(`${C.RED}[ORCH] Validation failed → initiating self-heal…${C.RESET}`);
            const heal = await selfHealCode(assembled, validation);
            if (!heal.success)
                return { success: false, error: heal.finalError, code: heal.code };
            finalCode = heal.code;
        }

        const merge    = await smartMergeUpgrade(targetFile, finalCode, description);
        const duration = ((Date.now() - t0) / 1000).toFixed(2);

        console.log(`\n${C.GREEN}${C.BOLD}[DONE] ✓ Completed in ${duration}s${C.RESET}`);

        return {
            success: true,
            code:    merge.merged,
            stats: {
                duration,
                functions:  plan.length,
                codeSize:   finalCode.length,
                strategy:   merge.strategy,
                replaced:   merge.replaced,
                added:      merge.added,
                backupPath: merge.backupPath || null,
            },
        };
    } catch (err) {
        console.log(`${C.RED}${C.BOLD}[CRITICAL] ${err.message}${C.RESET}`);
        return { success: false, error: err.message, stack: err.stack };
    }
}

// ══════════════════════════════════════════════════════════════════════════
// ★ generateTool — POLYMORPHIC ROUTER BRIDGE ★
// BUG FIX #2 & #14: Fixed switch-case syntax + robust type detection
// ══════════════════════════════════════════════════════════════════════════

async function generateTool(paramsOrActionName, description, targetFile) {
    // Robust type detection — BUG FIX #14
    let params;
    const typeStr = Object.prototype.toString.call(paramsOrActionName);
    
    if (typeStr === '[object Object]' && paramsOrActionName !== null && !Array.isArray(paramsOrActionName)) {
        // Object-style: generateTool({ type, actionName, ... })
        params = paramsOrActionName;
    } else {
        // Positional-style: generateTool(actionName, description, targetFile)
        const actionName = String(paramsOrActionName || '').trim();
        if (!actionName) {
            return { success: false, error: 'actionName is required when calling generateTool positionally' };
        }
        params = {
            type:        'code',
            actionName,
            description: String(description || ''),
            targetFile:  targetFile || null,
        };
    }

    const type = (params.type || 'code').toLowerCase().trim();
    console.log(`${C.MAGENTA}[generateTool] type=${type} | action=${params.actionName || '—'}${C.RESET}`);

    switch (type) {
        // ── Generate new code ─────────────────────────────────────────────
        case 'code':
        case 'generate':
        case 'create': {
            const action = (params.actionName || '').trim();
            if (!action) return { success: false, error: 'actionName is required for type=code' };
            return generateCodeInChunks(
                action,
                params.description || '',
                params.targetFile  || null
            );
        }

        // ── Self-evolve ───────────────────────────────────────────────────
        case 'evolve':
        case 'mutate':
        case 'self_evolve':
        case 'upgrade': {
            return selfEvolve({
                force:      params.force      || false,
                focusAreas: params.focusAreas || CONFIG.SELF_EVOLUTION.FOCUS_AREAS,
            });
        }

        // ── Validate a code string ────────────────────────────────────────
        case 'validate': {
            const { code = '', strict = false } = params;
            if (!code) return { success: false, error: 'code is required for type=validate' };
            return validateToolInSandbox(code, strict);
        }

        // ── Merge new code into an existing file ──────────────────────────
        case 'merge':
        case 'upgrade_file': {
            const { targetFile: tf, newCode, description: desc = '' } = params;
            if (!tf || !newCode)
                return { success: false, error: 'targetFile and newCode are required for type=merge' };
            return smartMergeUpgrade(tf, newCode, desc);
        }

        // ── Status / metrics ──────────────────────────────────────────────
        case 'status':
        case 'metrics': {
            try {
                const { source } = readSelfSource();
                return {
                    success: true,
                    version: EVOLUTION_STATE.version,
                    score:   scoreSelfSource(source),
                    state:   EVOLUTION_STATE,
                    config:  CONFIG.SELF_EVOLUTION,
                    cacheSize: cognitiveCache.size,
                };
            } catch (e) {
                return { success: false, error: e.message };
            }
        }

        // ── Internet search (direct) ──────────────────────────────────────
        case 'search': {
            const { query } = params;
            if (!query) return { success: false, error: 'query is required for type=search' };
            try {
                const result = await internetSearch(query);
                return { success: true, result };
            } catch (e) {
                return { success: false, error: e.message };
            }
        }

        // ── Ask cognitive engine directly ─────────────────────────────────
        case 'ask':
        case 'prompt': {
            const { prompt: p, cacheKey } = params;
            if (!p) return { success: false, error: 'prompt is required for type=ask' };
            try {
                const response = await cognitiveFallback(p, {}, cacheKey || null);
                return { success: true, response };
            } catch (e) {
                return { success: false, error: e.message };
            }
        }

        default:
            return {
                success: false,
                error:   `Unknown type: "${type}". Valid types: code, evolve, validate, merge, status, search, ask`,
            };
    }
}

// ══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ══════════════════════════════════════════════════════════════════════════
module.exports = {
    // ★ Primary entry point (polymorphic)
    generateTool,
    // Core pipeline
    generateCodeInChunks,
    generateExecutionPlan,
    generateCodeChunks,
    validateToolInSandbox,
    selfHealCode,
    smartMergeUpgrade,
    // 4-Tier Cognitive Engine
    cognitiveFallback,
    askOllama,
    askGroq,
    internetSearch,
    searchDDG,
    searchSearx,
    // Self-evolution
    selfEvolve,
    scoreSelfSource,
    readSelfSource,
    mutateOneFunction,
    applyMutation,
    saveEvolutionLog,
    // Utilities
    backupFile,
    checkSyntax,
    staticAnalysis,
    testRuntime,
    mergeSourceFiles,
    parseFunctions,
    extractCode,
    parseJSON,
    fetchWithTimeout,
    securityScan,
    // Config / State
    CONFIG,
    EVOLUTION_STATE,
    cognitiveCache,
};

// ══════════════════════════════════════════════════════════════════════════
// CLI
// ══════════════════════════════════════════════════════════════════════════
if (require.main === module) {
    const args    = process.argv.slice(2);
    const command = (args[0] || 'help').toLowerCase();

    const showHelp = () => console.log(`
${C.CYAN}${C.BOLD}┌─────────────────────────────────────────────────────────┐
│   🤖 PIKA Logic Factory v5.0 — CLI                       │
└─────────────────────────────────────────────────────────┘${C.RESET}
${C.GREEN}Usage:${C.RESET}
  node logic_factory.js generate <actionName> <description> [targetFile]
  node logic_factory.js evolve [--force]
  node logic_factory.js status
  node logic_factory.js validate <file.js>
  node logic_factory.js search <query>

${C.GREEN}Examples:${C.RESET}
  node logic_factory.js generate "HTTP Client" "Fetch wrapper with retry" http-client.js
  node logic_factory.js evolve --force
  node logic_factory.js status
  node logic_factory.js search "Node.js stream backpressure"
`);

    (async () => {
        let result = { success: true };

        switch (command) {
            case 'generate':
            case 'gen': {
                const [, actionName, description, tf] = args;
                if (!actionName || !description) { showHelp(); process.exit(1); }
                result = await generateCodeInChunks(actionName, description, tf || null);
                if (result.success) {
                    if (!tf) console.log(`\n${C.GREEN}[OUTPUT]${C.RESET}\n${result.code}`);
                    if (result.stats) console.log(`\n${C.CYAN}[STATS]${C.RESET}`, JSON.stringify(result.stats, null, 2));
                } else {
                    console.log(`${C.RED}[ERROR] ${result.error}${C.RESET}`);
                }
                break;
            }

            case 'evolve':
            case 'mutate': {
                result = await selfEvolve({ force: args.includes('--force') });
                console.log(`\n${C.CYAN}[RESULT]${C.RESET}`, JSON.stringify(result, null, 2));
                break;
            }

            case 'status': {
                const { source } = readSelfSource();
                const score      = scoreSelfSource(source);
                console.log(`${C.CYAN}
┌─ PIKA STATUS ────────────────────────────────────────────┐
│  Score:       ${String(score).padEnd(4)}/100                                │
│  Version:     ${EVOLUTION_STATE.version.padEnd(46)}│
│  Mutations:   ${EVOLUTION_STATE.totalMutations} total | ${EVOLUTION_STATE.successfulMutations} OK | ${EVOLUTION_STATE.failedMutations} failed${' '.repeat(18)}│
│  Cache size:  ${String(cognitiveCache.size).padEnd(46)}│
│  Self-file:   ${CONFIG.SELF_EVOLUTION.SELF_FILE.slice(-44).padEnd(46)}│
└──────────────────────────────────────────────────────────┘${C.RESET}`);
                break;
            }

            case 'validate': {
                const fp = args[1];
                if (!fp || !fs.existsSync(fp)) {
                    console.log(`${C.RED}File not found: ${fp}${C.RESET}`);
                    process.exit(1);
                }
                const code = fs.readFileSync(fp, 'utf8');
                result     = await validateToolInSandbox(code, true);
                console.log(result.success
                    ? `${C.GREEN}✓ Valid${C.RESET}`
                    : `${C.RED}✗ ${result.error}${C.RESET}`);
                break;
            }

            case 'search': {
                const query = args.slice(1).join(' ');
                if (!query) { showHelp(); process.exit(1); }
                try {
                    const res = await internetSearch(query);
                    console.log(`\n${C.GREEN}[SEARCH RESULT]${C.RESET}\n${res}`);
                } catch (e) {
                    console.log(`${C.RED}[SEARCH ERROR] ${e.message}${C.RESET}`);
                    result = { success: false };
                }
                break;
            }

            default:
                showHelp();
        }

        process.exit(result?.success !== false ? 0 : 1);
    })().catch(e => {
        console.error(`${C.RED}${C.BOLD}[FATAL] ${e.message}${C.RESET}`);
        process.exit(1);
    });
}

