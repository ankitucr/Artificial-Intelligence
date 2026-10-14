// ╔══════════════════════════════════════════════════════════════════════╗
// ║   🤖 PIKA — LOGIC FACTORY ENGINE v4.0                               ║
// ║   Self-Healing · Self-Mutating · 4-Tier Cognitive Fallback           ║
// ║   Designed for Termux/Android · Pure Node.js · Zero Heavy Deps       ║
// ╚══════════════════════════════════════════════════════════════════════╝
'use strict';

const fs   = require('fs');
const path = require('path');
const vm   = require('vm');

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

// Pretty banner helpers
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
    MAX_CYCLE_LOOPS:     3,          // full round-robin retries
    ENGINE_RETRIES:      3,          // retries per individual engine
    CHUNK_TIMEOUT:       30000,
    RUNTIME_TIMEOUT:     2500,
    PARALLEL_CHUNKS:     3,
    CACHE_ENABLED:       true,
    BACKUP_DIR:          'backups',

    MODELS: {
        PRIMARY_CODER:     'qwen2.5-coder:1.3b',
        REASONING:         'deepseek-r1:1.5b',
        FALLBACK_CODER:    'qwen2.5-coder:7b',
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
};

// ══════════════════════════════════════════════════════════════════════════
// COGNITIVE CACHE (in-memory)
// ══════════════════════════════════════════════════════════════════════════
const cognitiveCache = new Map();

const EVOLUTION_STATE = {
    totalMutations:      0,
    successfulMutations: 0,
    failedMutations:     0,
    cycleHistory:        [],
    lastScore:           0,
    version:             '4.0',
};

// ══════════════════════════════════════════════════════════════════════════
// UTILITY — fetch with timeout
// ══════════════════════════════════════════════════════════════════════════
async function fetchWithTimeout(url, opts = {}, timeoutMs = CONFIG.CHUNK_TIMEOUT) {
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
        const res = await fetch(url, { ...opts, signal: ctrl.signal });
        clearTimeout(tid);
        return res;
    } catch (e) {
        clearTimeout(tid);
        throw e;
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
// ENGINE 4 — Internet Search (DuckDuckGo Instant Answer + HTML scrape)
// ══════════════════════════════════════════════════════════════════════════

/**
 * Strip HTML tags and decode common entities from a string.
 */
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

/**
 * Extract <pre> / <code> blocks from raw HTML as potential code snippets.
 */
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

/**
 * Search DuckDuckGo Instant Answer API.
 * Returns a plain-text summary string or throws.
 */
async function searchDDG(query) {
    const url = `${CONFIG.SEARCH.DDG_URL}?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
    const res = await fetchWithTimeout(url, {
        headers: { 'User-Agent': 'Pika-AGI/4.0 Node.js' },
    }, CONFIG.SEARCH.TIMEOUT);

    if (!res.ok) throw new Error(`DDG HTTP ${res.status}`);
    const data = await res.json();

    const parts = [
        data.AbstractText,
        data.Answer,
        (data.Results  || []).slice(0, 3).map(r => r.Text).join(' '),
        (data.RelatedTopics || []).slice(0, 3).map(t => t.Text).join(' '),
    ].filter(Boolean);

    if (!parts.length) throw new Error('DDG returned no useful content');
    return parts.join('\n').trim();
}

/**
 * Fallback: fetch a raw search result page from Searx and extract code blocks.
 */
async function searchSearx(query) {
    const url = `${CONFIG.SEARCH.SEARX_URL}?q=${encodeURIComponent(query)}&format=html&categories=it`;
    const res = await fetchWithTimeout(url, {
        headers: { 'User-Agent': 'Pika-AGI/4.0 Node.js', 'Accept': 'text/html' },
    }, CONFIG.SEARCH.TIMEOUT);

    if (!res.ok) throw new Error(`Searx HTTP ${res.status}`);
    const html   = await res.text();
    const blocks = extractCodeBlocks(html);
    if (!blocks.length) {
        // Fall back to plain text summary of page
        const plain = stripHtml(html).slice(0, 2000);
        if (plain.length < 50) throw new Error('Searx returned no useful content');
        return plain;
    }
    return blocks.slice(0, 5).join('\n\n---\n\n');
}

/**
 * Combined search: tries DDG first, then Searx.
 */
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
// 4-TIER COGNITIVE FALLBACK ENGINE
// ══════════════════════════════════════════════════════════════════════════

/**
 * Tier definitions — executed in this order per round-robin cycle.
 */
function buildTiers(prompt, opts = {}) {
    return [
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
            // For search, we convert the coding prompt to a concise query
            call:   () => {
                const q = (opts.searchQuery)
                    || prompt.slice(0, 300).replace(/\n/g, ' ').trim();
                return internetSearch(q);
            },
        },
    ];
}

/**
 * ★ MASTER COGNITIVE CALL ★
 *
 * Checks cognitive cache first, then runs the 4-tier round-robin loop.
 * Each engine gets ENGINE_RETRIES attempts. On total failure of all engines,
 * repeats the full cycle up to MAX_CYCLE_LOOPS times.
 *
 * @param {string}   prompt   - The prompt / query to send
 * @param {Object}   opts     - Extra options passed to engines
 * @param {string}   cacheKey - If set, results are cached under this key
 * @returns {Promise<string>} - Raw LLM / search response
 */
async function cognitiveFallback(prompt, opts = {}, cacheKey = null) {
    // ── Step 1: Check Cognitive Cache ────────────────────────────────────
    if (cacheKey && CONFIG.CACHE_ENABLED && cognitiveCache.has(cacheKey)) {
        engineLog('CACHE', `Cache hit → ${cacheKey}`, 'ok');
        return cognitiveCache.get(cacheKey);
    }

    const tiers = buildTiers(prompt, opts);

    // ── Step 2: Round-Robin Loop ──────────────────────────────────────────
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
                    if (cacheKey && CONFIG.CACHE_ENABLED)
                        cognitiveCache.set(cacheKey, response);

                    console.log(`${C.MAGENTA}${C.BOLD}└──────────────────────────────────────────────────────┘${C.RESET}`);
                    return response;
                } catch (err) {
                    lastErr = err;
                    engineLog(tier.name, `Attempt ${attempt} failed: ${err.message}`, 'warn');
                    if (attempt < CONFIG.ENGINE_RETRIES)
                        await new Promise(r => setTimeout(r, 800 * attempt)); // backoff
                }
            }

            engineLog(tier.name, `All ${CONFIG.ENGINE_RETRIES} attempts exhausted — shifting engine`, 'shift');
        }

        console.log(`${C.RED}${C.BOLD}│  ✗ All 4 engines failed on cycle ${cycle}. ${cycle < CONFIG.MAX_CYCLE_LOOPS ? 'Retrying cycle…' : 'CRITICAL FAILURE.'}${C.RESET}`);
        console.log(`${C.MAGENTA}${C.BOLD}└──────────────────────────────────────────────────────┘${C.RESET}`);

        if (cycle < CONFIG.MAX_CYCLE_LOOPS)
            await new Promise(r => setTimeout(r, 2000 * cycle));
    }

    throw new Error(`[PIKA] CRITICAL: All ${CONFIG.MAX_CYCLE_LOOPS} cognitive cycles exhausted across all 4 engines.`);
}

// ══════════════════════════════════════════════════════════════════════════
// CODE EXTRACTION
// ══════════════════════════════════════════════════════════════════════════
function extractCode(raw) {
    let cleaned = raw
        .replace(/```(?:javascript|js|typescript|ts|node)?\n?/g, '')
        .replace(/```/g, '');

    cleaned = cleaned
        .replace(/^(?:Here's|This is|The following|Below is|Sure[,!]?).*?:\s*/gim, '')
        .replace(/^(?:Note|Important|Warning|Explanation):.*$/gim, '');

    return cleaned
        .split('\n')
        .filter(line => {
            const t = line.trim();
            return t && !t.match(/^(Let me|I'll|To |This |The |You can|Here is)/i);
        })
        .join('\n')
        .trim();
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
// BACKUP SYSTEM
// ══════════════════════════════════════════════════════════════════════════
function ensureBackupDir() {
    const dir = path.resolve(process.cwd(), CONFIG.BACKUP_DIR);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    return dir;
}

/**
 * Create a timestamped backup before any file mutation.
 * @param {string} filePath
 * @returns {{ success: boolean, backupPath?: string, error?: string }}
 */
function backupFile(filePath) {
    const abs = path.resolve(process.cwd(), filePath);
    if (!fs.existsSync(abs))
        return { success: true, backupPath: null, note: 'New file — no backup needed' };

    try {
        const dir     = ensureBackupDir();
        const ext     = path.extname(abs);
        const base    = path.basename(abs, ext);
        const ts      = new Date().toISOString().replace(/[:.]/g, '-');
        const bkpPath = path.join(dir, `${base}.${ts}.backup${ext}`);
        fs.copyFileSync(abs, bkpPath);
        console.log(`${C.GREEN}[BACKUP] ✓ → ${bkpPath}${C.RESET}`);
        return { success: true, backupPath: bkpPath };
    } catch (err) {
        const msg = `Backup failed: ${err.message}`;
        console.log(`${C.RED}[BACKUP] ✗ ${msg}${C.RESET}`);
        return { success: false, error: msg };
    }
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
        const raw  = await cognitiveFallback(prompt, { temperature: 0.3, timeout: 20000,
            searchQuery: `Node.js implementation plan for: ${actionName}` }, cacheKey + '_raw');
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
    const header = `// ═══ Auto-generated by Pika Logic Factory v4.0 — ${new Date().toISOString()} ═══\n\n`;
    return header + chunks
        .sort((a, b) => (a.priority || 2) - (b.priority || 2))
        .map(c => `// ── ${c.name} ──────────────────────────────────────\n${c.code}`)
        .join('\n\n') + '\n';
}

// ══════════════════════════════════════════════════════════════════════════
// PHASE 3 — SANDBOX VALIDATION
// ══════════════════════════════════════════════════════════════════════════
async function validateToolInSandbox(code, strict = false) {
    phase(3, 'SANDBOX VALIDATION');

    const syntax = checkSyntax(code);
    if (!syntax.valid) return { success: false, error: syntax.error, layer: 'syntax', code };
    console.log(`${C.GREEN}  ✓ Syntax OK${C.RESET}`);

    const stat = staticAnalysis(code);
    if (!stat.safe) return { success: false, error: stat.error, layer: 'static', code };
    console.log(`${C.GREEN}  ✓ Static analysis OK${C.RESET}`);

    if (strict) {
        const rt = testRuntime(code);
        if (!rt.success)
            return { success: false, error: rt.error, output: rt.output, layer: 'runtime', code };
        console.log(`${C.GREEN}  ✓ Runtime OK${rt.output ? ' | ' + rt.output : ''}${C.RESET}`);
    }

    return { success: true, code };
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

function staticAnalysis(code) {
    const dangerous = [
        [/\beval\s*\(/g,            'eval()'],
        [/\bFunction\s*\(/g,        'Function constructor'],
        [/child_process/g,           'child_process'],
        [/__proto__/g,               'prototype pollution'],
        [/process\.exit/g,           'process.exit()'],
        [/require\s*\(\s*['"]fs/g,   'fs in generated code'],
    ];
    for (const [pat, name] of dangerous)
        if (pat.test(code)) return { safe: false, error: `Dangerous pattern: ${name}` };
    if (code.trim().length < 10) return { safe: false, error: 'Code too short' };
    return { safe: true };
}

function testRuntime(code) {
    const logs = [], errs = [];
    const sandbox = {
        console: {
            log:   (...a) => logs.push(a.map(String).join(' ')),
            warn:  (...a) => logs.push('[W] ' + a.map(String).join(' ')),
            error: (...a) => errs.push(a.map(String).join(' ')),
        },
        setTimeout: () => {}, setInterval: () => {}, clearTimeout: () => {},
        Math, JSON, Array, Object, String, Number, Boolean, Date, Error, Map, Set, Promise,
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
            const raw      = await cognitiveFallback(prompt, { temperature: 0.1, timeout: 22000,
                searchQuery: `Fix JavaScript ${vr.layer} error: ${vr.error}` });
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
// PHASE 5 — SMART MERGE (File Mutation)
// ══════════════════════════════════════════════════════════════════════════

/**
 * Parse all top-level named function declarations from source.
 * Returns Map<name, fullBodyString>.
 */
function parseFunctions(source) {
    const map   = new Map();
    const regex = /^(?:\/\*[\s\S]*?\*\/\s*)?(?:async\s+)?function\s+(\w+)\s*\(/gm;
    let m;

    while ((m = regex.exec(source)) !== null) {
        const name  = m[1];
        const start = source.indexOf('{', m.index + m[0].length - 1);
        if (start === -1) continue;

        let depth = 0, i = start;
        for (; i < source.length; i++) {
            if (source[i] === '{') depth++;
            else if (source[i] === '}' && --depth === 0) break;
        }

        const cs = findPrecedingComment(source, m.index);
        map.set(name, source.slice(cs, i + 1).trim());
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

/**
 * Merge new functions into existing source:
 * - Replace functions that already exist
 * - Append brand-new functions
 */
function mergeSourceFiles(existing, newSrc) {
    const existFns = parseFunctions(existing);
    const newFns   = parseFunctions(newSrc);
    const replaced = [], added = [];
    let merged     = existing;

    for (const [name, body] of newFns) {
        if (existFns.has(name)) {
            merged = merged.replace(existFns.get(name), body);
            replaced.push(name);
        } else {
            merged += `\n\n// ── ${name} (added by Pika v4.0) ──\n${body}`;
            added.push(name);
        }
    }
    return { merged, replaced, added };
}

/**
 * Full Phase 5: read → backup → merge → write.
 */
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

    const bkp = backupFile(abs);
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
// ★ SELF-EVOLUTION ENGINE ★
// ══════════════════════════════════════════════════════════════════════════

function readSelfSource() {
    const selfPath = CONFIG.SELF_EVOLUTION.SELF_FILE;
    if (!fs.existsSync(selfPath))
        throw new Error(`Self-file not found: ${selfPath}`);
    return { source: fs.readFileSync(selfPath, 'utf8'), path: selfPath };
}

/**
 * Score engine source quality 0–100.
 */
function scoreSelfSource(source) {
    let score    = 100;
    const fns    = (source.match(/^(?:async\s+)?function\s+\w+/gm) || []).length;
    const tries  = (source.match(/try\s*\{/g) || []).length;
    const jsdocs = (source.match(/\/\*\*[\s\S]*?\*\//g) || []).length;
    const longFn = (source.match(/function\s+\w+[^}]{3200,}/g) || []).length;

    if (fns > 0 && tries  / fns < 0.4) score -= 15;
    if (fns > 0 && jsdocs / fns < 0.3) score -= 10;
    score -= longFn * 5;
    if (source.includes("'use strict'"))   score += 2;
    if (source.includes('module.exports')) score += 3;

    return Math.max(0, Math.min(100, score));
}

/**
 * Ask the cognitive engine to improve one specific function body.
 */
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
        const raw   = await cognitiveFallback(prompt, { temperature: 0.2, timeout: 25000,
            searchQuery: `Improve Node.js ${focusArea} for function ${funcName}` });
        const clean = extractCode(raw);
        if (!clean || clean.length < 30) return null;
        return clean;
    } catch (e) {
        console.log(`${C.RED}[MUTATE] Engine failed for ${funcName}: ${e.message}${C.RESET}`);
        return null;
    }
}

/**
 * Apply an improved function body back into the full source string.
 * Validates syntax before and after. Returns new source or null.
 */
function applyMutation(source, funcName, newFuncBody) {
    const fns = parseFunctions(source);
    if (!fns.has(funcName)) return null;

    if (!checkSyntax(newFuncBody).valid) {
        console.log(`${C.RED}[MUTATE] Syntax invalid for ${funcName}${C.RESET}`);
        return null;
    }

    const newSource = source.replace(fns.get(funcName), newFuncBody);

    if (!checkSyntax(newSource).valid) {
        console.log(`${C.RED}[MUTATE] File syntax broken after mutating ${funcName}${C.RESET}`);
        return null;
    }

    return newSource;
}

/**
 * Persist evolution log entry to JSON file on disk.
 */
function saveEvolutionLog(entry) {
    const logPath = path.resolve(process.cwd(), CONFIG.SELF_EVOLUTION.EVOLUTION_LOG);
    let history   = [];
    if (fs.existsSync(logPath)) {
        try { history = JSON.parse(fs.readFileSync(logPath, 'utf8')); } catch (_) {}
    }
    history.push({ timestamp: new Date().toISOString(), ...entry });
    if (history.length > 500) history = history.slice(-500);
    fs.writeFileSync(logPath, JSON.stringify(history, null, 2), 'utf8');
}

/**
 * ★ MAIN SELF-EVOLUTION CYCLE ★
 *
 * 1. Reads own source code
 * 2. Scores quality
 * 3. Picks functions to improve
 * 4. Uses 4-tier cognitive engine to rewrite them
 * 5. Validates each mutation
 * 6. Writes improved source back to disk
 */
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
        .filter(n => (allFns.get(n) || '').split('\n').length > 5)
        .slice(0, cfg.MAX_MUTATIONS_PER_CYCLE);

    if (!targets.length) {
        console.log(`${C.YELLOW}[EVOLVE] No suitable mutation targets${C.RESET}`);
        return { success: false, reason: 'no_targets' };
    }

    console.log(`${C.YELLOW}[EVOLVE] Targets: ${targets.join(', ')}${C.RESET}`);

    const bkp = backupFile(selfPath);
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
        const funcBody = parseFunctions(currentSrc).get(funcName);
        if (!funcBody) continue;

        console.log(`${C.YELLOW}[MUTATE] ${funcName} → focus: ${focus}${C.RESET}`);
        EVOLUTION_STATE.totalMutations++;

        const improved = await mutateOneFunction(funcName, funcBody, focus);

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
    EVOLUTION_STATE.cycleHistory.push({ ts: Date.now(), scoreBefore, scoreAfter, ok, fail });

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
    const t0 = Date.now();
    console.log(`\n${C.GREEN}${C.BOLD}╔════════════════════════════════════════════════════╗`);
    console.log(`║   🚀  PIKA LOGIC FACTORY v4.0 — ACTIVATED          ║`);
    console.log(`╚════════════════════════════════════════════════════╝${C.RESET}`);
    console.log(`${C.CYAN}  Action:      ${actionName}${C.RESET}`);
    console.log(`${C.CYAN}  Description: ${description}${C.RESET}`);
    console.log(`${C.CYAN}  Target:      ${targetFile || '(new file)'}${C.RESET}`);

    try {
        const plan = await generateExecutionPlan(actionName, description, targetFile);
        if (!plan?.length) throw new Error('Empty execution plan returned');

        const assembled = await generateCodeChunks(plan, { actionName, description });

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
//
// Accepts EITHER:
//   generateTool({ type: 'code', actionName: '...', description: '...' })
//   generateTool(actionName, description, targetFile)   ← positional strings
//
// evolution_engine.js can call either form — both work correctly.
// ══════════════════════════════════════════════════════════════════════════

/**
 * Universal router entrypoint.
 *
 * @param {Object|string} paramsOrActionName  - Object params OR positional string
 * @param {string}        [description]       - Used when called positionally
 * @param {string}        [targetFile]        - Used when called positionally
 * @returns {Promise<Object>}
 */
async function generateTool(paramsOrActionName, description, targetFile) {
    // ── Polymorphic signature detection ──────────────────────────────────
    let params;

    if (paramsOrActionName && typeof paramsOrActionName === 'object' && !Array.isArray(paramsOrActionName)) {
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
│   🤖 PIKA Logic Factory v4.0 — CLI                       │
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
