// ══════════════════════════════════════════════════════════════════════════
// 🧬 ADVANCED MUTATION ENGINE v3.0 (FIXED: validate-before-write, real
// sandbox isolation, large-file safety, shared cross-system lock)
// ══════════════════════════════════════════════════════════════════════════

const fs = require('fs-extra');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');
const { trackAction } = require('./tracker.js');

// 📂 DYNAMIC PATHS
const BACKUP_DIR       = path.join(__dirname, '../backups');
const BASE_DIR         = path.join(__dirname, '../');
const DATA_DIR         = path.join(__dirname, '../data');
const DATASET_VAULT    = path.join(DATA_DIR, 'dataset_vault.jsonl');
const MUTATION_HISTORY = path.join(DATA_DIR, 'mutation_history.json');

// 🔒 NEW: same shared lock file used by evolution_engine.js
const MUTATION_LOCK_FILE = path.join(DATA_DIR, 'mutation_lock.json');

// 🎨 TERMINAL COLORS
const C = {
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m",
    YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", BLUE: "\x1b[34m",
    MAGENTA: "\x1b[35m", RESET: "\x1b[0m", BOLD: "\x1b[1m", DIM: "\x1b[2m"
};

// ==========================================
// Configuration
// ==========================================
const CONFIG = {
    MAX_BACKUP_RETENTION: 10,
    MIN_CODE_LENGTH: 50,
    MAX_FILE_SIZE: 500000,           // 500KB max file size
    // NEW: above this size, skip Levenshtein (too slow) and use a fast
    // hash+length based similarity heuristic instead
    LEVENSHTEIN_SAFE_LIMIT: 20000,   // ~20KB — beyond this, O(n*m) gets dangerous
    SIMILARITY_THRESHOLD: 0.95,
    AUTO_CLEANUP_DAYS: 7,
    ENABLE_DEEP_SCAN: true,
    ENABLE_METRICS: true,
    RUNTIME_TIMEOUT: 5000,
    // NEW: safe modules whitelist for sandbox — no full require() escape hatch
    SANDBOX_SAFE_MODULES: new Set([
        'path', 'url', 'querystring', 'crypto', 'util', 'stream', 'events',
        'string_decoder', 'punycode', 'os', 'buffer'
    ]),
    PROTECTED_PATTERNS: [
        /API_KEY/i,
        /SECRET/i,
        /PASSWORD/i,
        /process\.env\./
    ]
};

class MutationEngine {
    constructor() {
        this.metrics = {
            totalMutations: 0,
            successful: 0,
            failed: 0,
            rollbacks: 0,
            rejected: 0
        };
        this.mutationHistory = new Map();
        this.initialize();
    }

    // ==========================================
    // 🔧 INITIALIZATION
    // ==========================================
    async initialize() {
        try {
            await fs.ensureDir(BACKUP_DIR);
            await fs.ensureDir(path.dirname(DATASET_VAULT));
            await fs.ensureDir(path.dirname(MUTATION_HISTORY));

            if (await fs.pathExists(MUTATION_HISTORY)) {
                const data = await fs.readJson(MUTATION_HISTORY);
                this.metrics = data.metrics || this.metrics;
                if (data.history) {
                    this.mutationHistory = new Map(Object.entries(data.history));
                }
            }

            if (CONFIG.AUTO_CLEANUP_DAYS > 0) {
                this.scheduleBackupCleanup();
            }

            console.log(`${C.GREEN}[MUTATION ENGINE v3.0]${C.RESET} Initialized successfully`);
        } catch (error) {
            console.error(`${C.RED}[INIT ERROR]${C.RESET} ${error.message}`);
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 🔒 NEW: SHARED MUTATION LOCK — coordinates with evolution_engine.js
    // and autonomous_mutator.js so two systems never edit files at once
    // ══════════════════════════════════════════════════════════════════════
    async acquireLock(owner = 'mutation_service') {
        try {
            await fs.ensureDir(DATA_DIR);
            if (await fs.pathExists(MUTATION_LOCK_FILE)) {
                const lock = await fs.readJson(MUTATION_LOCK_FILE).catch(() => null);
                const STALE_MS = 10 * 60 * 1000; // 10 min stale lock protection
                if (lock && lock.locked && (Date.now() - lock.timestamp) < STALE_MS) {
                    console.log(`${C.YELLOW}[LOCK]${C.RESET} Held by '${lock.owner}' — cannot mutate right now.`);
                    return false;
                }
            }
            await fs.writeJson(MUTATION_LOCK_FILE, { locked: true, owner, timestamp: Date.now() }, { spaces: 2 });
            return true;
        } catch (e) {
            console.error(`${C.RED}[LOCK ERROR]${C.RESET} ${e.message}`);
            return false; // fail-safe: don't mutate if lock system is broken
        }
    }

    async releaseLock() {
        try {
            await fs.writeJson(MUTATION_LOCK_FILE, { locked: false, owner: null, timestamp: Date.now() }, { spaces: 2 });
        } catch (e) {
            console.error(`${C.RED}[LOCK RELEASE ERROR]${C.RESET} ${e.message}`);
        }
    }

    // ==========================================
    // 🛡️ SECURITY SHIELD (unchanged — was correct)
    // ==========================================
    isSafeToEdit(targetPath) {
        const fileName = path.basename(targetPath);
        const normalizedPath = path.normalize(targetPath);

        const protectedFiles = [
            '.env', '.env.local', '.env.production', 'server.js',
            'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            '.git', '.gitignore'
        ];

        if (protectedFiles.includes(fileName)) {
            console.log(`\n${C.RED}${C.BOLD}[SHIELD ACTIVE]${C.RESET} Access Denied: ${C.CYAN}${fileName}${C.RESET} is a core system file.`);
            return { safe: false, reason: 'Protected core file' };
        }

        const protectedDirs = ['backups', 'data', 'node_modules', 'logs', '.git', 'dist', 'build'];

        for (const dir of protectedDirs) {
            if (normalizedPath.includes(path.sep + dir + path.sep) ||
                normalizedPath.endsWith(path.sep + dir)) {
                console.log(`\n${C.RED}${C.BOLD}[SHIELD ACTIVE]${C.RESET} Access Denied: Protected directory ${C.CYAN}${dir}${C.RESET}`);
                return { safe: false, reason: `Protected directory: ${dir}` };
            }
        }

        const ext = path.extname(fileName);
        const allowedExtensions = ['.js', '.ts', '.jsx', '.tsx', '.json', '.html', '.css', '.md'];

        if (ext && !allowedExtensions.includes(ext)) {
            console.log(`\n${C.YELLOW}[WARNING]${C.RESET} File type ${ext} requires manual review`);
            return { safe: false, reason: `Unsupported file type: ${ext}` };
        }

        return { safe: true, reason: 'File is safe to edit' };
    }

    // ==========================================
    // 📊 DIFF ANALYSIS — NOW SIZE-AWARE
    // ==========================================
    async analyzeDiff(oldCode, newCode, targetFile) {
        const analysis = {
            valid: false, reason: '', metrics: {}, warnings: [], severity: 'info'
        };

        if (!newCode || newCode.trim().length === 0) {
            analysis.reason = "Empty code block received from API";
            analysis.severity = 'critical';
            return analysis;
        }

        if (!oldCode) {
            analysis.valid = true;
            analysis.reason = "New file creation";
            return analysis;
        }

        const oldLen = oldCode.length;
        const newLen = newCode.length;

        // FIXED: pick similarity strategy based on file size to avoid hangs
        const similarity = this.calculateSimilarity(oldCode, newCode);
        analysis.metrics.similarity = similarity;
        analysis.metrics.oldLength = oldLen;
        analysis.metrics.newLength = newLen;
        analysis.metrics.lengthDelta = newLen - oldLen;
        analysis.metrics.lengthRatio = newLen / oldLen;

        if (similarity >= CONFIG.SIMILARITY_THRESHOLD) {
            analysis.reason = `No meaningful changes detected (${(similarity * 100).toFixed(1)}% similarity)`;
            analysis.severity = 'warning';
            return analysis;
        }

        if (newLen < (oldLen * 0.6) && oldLen > CONFIG.MIN_CODE_LENGTH) {
            analysis.reason = `Code size reduced by ${((1 - newLen/oldLen) * 100).toFixed(1)}% - possible truncation`;
            analysis.severity = 'critical';
            return analysis;
        }

        if (newLen < CONFIG.MIN_CODE_LENGTH) {
            analysis.reason = `Code too small (${newLen} chars) - minimum ${CONFIG.MIN_CODE_LENGTH} required`;
            analysis.severity = 'error';
            return analysis;
        }

        if (targetFile.endsWith('.js') || targetFile.endsWith('.ts')) {
            const oldHasExports = oldCode.includes('module.exports') || oldCode.includes('export ');
            const newHasExports = newCode.includes('module.exports') || newCode.includes('export ');

            if (oldHasExports && !newHasExports) {
                analysis.reason = "Critical: Module exports removed - will break imports";
                analysis.severity = 'critical';
                return analysis;
            }
        }

        for (const pattern of CONFIG.PROTECTED_PATTERNS) {
            const oldMatches = (oldCode.match(pattern) || []).length;
            const newMatches = (newCode.match(pattern) || []).length;
            if (oldMatches > 0 && newMatches === 0) {
                analysis.warnings.push(`Protected pattern ${pattern} removed`);
            }
        }

        const structureCheck = this.checkStructuralIntegrity(oldCode, newCode);
        if (!structureCheck.valid) {
            analysis.reason = structureCheck.reason;
            analysis.severity = 'error';
            return analysis;
        }

        const oldCommentRatio = this.calculateCommentRatio(oldCode);
        const newCommentRatio = this.calculateCommentRatio(newCode);

        if (newCommentRatio > 0.7 && oldCommentRatio < 0.3) {
            analysis.warnings.push('High comment ratio - possible AI explanation instead of code');
        }

        analysis.valid = true;
        analysis.reason = `Valid mutation: ${(similarity * 100).toFixed(1)}% similarity, ${analysis.metrics.lengthDelta > 0 ? '+' : ''}${analysis.metrics.lengthDelta} chars`;

        return analysis;
    }

    // ==========================================
    // 🧮 SIMILARITY — FIXED: size-gated algorithm choice
    // ==========================================
    calculateSimilarity(str1, str2) {
        const normalize = (s) => s.replace(/\s+/g, ' ').trim().toLowerCase();
        const s1 = normalize(str1);
        const s2 = normalize(str2);

        if (s1 === s2) return 1.0;

        const maxLen = Math.max(s1.length, s2.length);
        if (maxLen === 0) return 1.0;

        // FIXED: Levenshtein is O(n*m) — a 500KB file would mean ~2.5×10^11
        // operations and hang the process. Above the safe limit, fall back
        // to a fast chunk-hash comparison instead.
        if (maxLen > CONFIG.LEVENSHTEIN_SAFE_LIMIT) {
            return this.fastApproxSimilarity(s1, s2);
        }

        const distance = this.levenshteinDistance(s1, s2);
        return 1 - (distance / maxLen);
    }

    // NEW: fast O(n) approximate similarity for large files —
    // compares fixed-size chunk hashes instead of full edit distance
    fastApproxSimilarity(s1, s2) {
        const CHUNK = 200;
        const hashChunks = (s) => {
            const chunks = [];
            for (let i = 0; i < s.length; i += CHUNK) {
                chunks.push(crypto.createHash('md5').update(s.slice(i, i + CHUNK)).digest('hex'));
            }
            return chunks;
        };

        const c1 = hashChunks(s1);
        const c2 = hashChunks(s2);
        const maxChunks = Math.max(c1.length, c2.length);
        if (maxChunks === 0) return 1.0;

        let matches = 0;
        const minChunks = Math.min(c1.length, c2.length);
        for (let i = 0; i < minChunks; i++) {
            if (c1[i] === c2[i]) matches++;
        }

        return matches / maxChunks;
    }

    // ==========================================
    // 📏 LEVENSHTEIN DISTANCE (only used below safe limit now)
    // ==========================================
    levenshteinDistance(str1, str2) {
        const len1 = str1.length;
        const len2 = str2.length;
        const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));

        for (let i = 0; i <= len1; i++) matrix[i][0] = i;
        for (let j = 0; j <= len2; j++) matrix[0][j] = j;

        for (let i = 1; i <= len1; i++) {
            for (let j = 1; j <= len2; j++) {
                const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
                matrix[i][j] = Math.min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + cost
                );
            }
        }

        return matrix[len1][len2];
    }

    // ==========================================
    // 🏗️ STRUCTURAL INTEGRITY CHECK (unchanged)
    // ==========================================
    checkStructuralIntegrity(oldCode, newCode) {
        const countChars = (str, char) => (str.match(new RegExp(`\\${char}`, 'g')) || []).length;

        const checks = [
            { char: '{', closing: '}', name: 'curly braces' },
            { char: '[', closing: ']', name: 'square brackets' },
            { char: '(', closing: ')', name: 'parentheses' }
        ];

        for (const check of checks) {
            const newOpen = countChars(newCode, check.char);
            const newClose = countChars(newCode, check.closing);

            if (newOpen !== newClose) {
                return { valid: false, reason: `Unbalanced ${check.name}: ${newOpen} opening, ${newClose} closing` };
            }
        }

        return { valid: true, reason: 'Structure intact' };
    }

    // ==========================================
    // 💬 COMMENT RATIO (unchanged)
    // ==========================================
    calculateCommentRatio(code) {
        const commentLines = (code.match(/\/\/.*$/gm) || []).length +
                            (code.match(/\/\*[\s\S]*?\*\//g) || []).length;
        const totalLines = code.split('\n').filter(l => l.trim()).length;
        return totalLines > 0 ? commentLines / totalLines : 0;
    }

    // ==========================================
    // 🧠 BRAIN READ (unchanged)
    // ==========================================
    async readBrain(targetFile) {
        try {
            const fullPath = path.join(BASE_DIR, targetFile);
            if (!(await fs.pathExists(fullPath))) {
                throw new Error(`File does not exist: ${targetFile}`);
            }

            const stats = await fs.stat(fullPath);
            if (stats.size > CONFIG.MAX_FILE_SIZE) {
                throw new Error(`File too large: ${(stats.size / 1024).toFixed(2)}KB (max ${CONFIG.MAX_FILE_SIZE / 1024}KB)`);
            }

            let code = await fs.readFile(fullPath, 'utf8');
            const warnings = [];
            if (code.length > 15000) warnings.push('FILE_SIZE_WARNING');
            if (this.calculateCommentRatio(code) < 0.1) warnings.push('LOW_DOCUMENTATION');

            return { code, size: stats.size, lines: code.split('\n').length, warnings, hash: this.hashCode(code) };
        } catch (err) {
            throw new Error(`Brain read failed: ${err.message}`);
        }
    }

    hashCode(code) {
        return crypto.createHash('sha256').update(code).digest('hex').substring(0, 16);
    }

    // ==========================================
    // 📝 VAULT LOGGING (unchanged)
    // ==========================================
    async logToVault(targetFile, status, details) {
        try {
            const entry = {
                timestamp: new Date().toISOString(), type: "MUTATION_RECORD",
                file: targetFile, status, details,
                hash: details.newHash || null, metrics: details.metrics || null
            };
            await fs.appendFile(DATASET_VAULT, JSON.stringify(entry) + '\n', 'utf8');
        } catch (e) {
            console.error(`${C.RED}[VAULT ERROR]${C.RESET} ${e.message}`);
        }
    }

    // ==========================================
    // 💾 BACKUP SYSTEM (unchanged)
    // ==========================================
    async createBackup(targetFile, code) {
        const fileName = path.basename(targetFile);
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const hash = this.hashCode(code).substring(0, 8);
        const backupPath = path.join(BACKUP_DIR, `${fileName}_${timestamp}_${hash}.bak`);

        await fs.writeFile(backupPath, code, 'utf8');
        await this.cleanupOldBackups(fileName);
        return backupPath;
    }

    async cleanupOldBackups(fileName) {
        try {
            const allBackups = await fs.readdir(BACKUP_DIR);
            const fileBackups = allBackups
                .filter(f => f.startsWith(fileName))
                .map(f => ({ name: f, path: path.join(BACKUP_DIR, f), time: fs.statSync(path.join(BACKUP_DIR, f)).mtime }))
                .sort((a, b) => b.time - a.time);

            if (fileBackups.length > CONFIG.MAX_BACKUP_RETENTION) {
                const toDelete = fileBackups.slice(CONFIG.MAX_BACKUP_RETENTION);
                for (const backup of toDelete) {
                    await fs.remove(backup.path);
                    console.log(`${C.DIM}[CLEANUP] Removed old backup: ${backup.name}${C.RESET}`);
                }
            }
        } catch (error) {
            console.error(`${C.YELLOW}[CLEANUP WARNING]${C.RESET} ${error.message}`);
        }
    }

    scheduleBackupCleanup() {
        setInterval(async () => {
            try {
                const cutoffDate = new Date();
                cutoffDate.setDate(cutoffDate.getDate() - CONFIG.AUTO_CLEANUP_DAYS);

                const backups = await fs.readdir(BACKUP_DIR);
                let deletedCount = 0;

                for (const backup of backups) {
                    const backupPath = path.join(BACKUP_DIR, backup);
                    const stats = await fs.stat(backupPath);
                    if (stats.mtime < cutoffDate) {
                        await fs.remove(backupPath);
                        deletedCount++;
                    }
                }

                if (deletedCount > 0) {
                    console.log(`${C.GREEN}[AUTO-CLEANUP]${C.RESET} Removed ${deletedCount} old backup(s)`);
                }
            } catch (error) {
                console.error(`${C.RED}[AUTO-CLEANUP ERROR]${C.RESET} ${error.message}`);
            }
        }, 24 * 60 * 60 * 1000);
    }

    // ══════════════════════════════════════════════════════════════════════
    // 🔬 SANDBOX VALIDATION — FIXED: real isolation, no live require() escape
    // ══════════════════════════════════════════════════════════════════════
    // OLD BUG: this used `require(testPath)` to "test" the module — but
    // require() is REAL Node.js execution with full fs/network/process
    // access. That's not a sandbox at all, and it ran AFTER the file was
    // already written to disk, so a malicious/broken module could act
    // before rollback ever happened.
    //
    // FIXED: validate the code as a STRING first (before any disk write),
    // using vm.createContext with a whitelisted module set — same pattern
    // as logic_factory.js's testRuntime(). No real require(), no disk I/O
    // happens until validation passes.
    validateInSandbox(code) {
        console.log(`${C.YELLOW}[VALIDATION]${C.RESET} Running sandbox tests (isolated, pre-write)...`);

        try {
            // Test 1: Syntax
            new vm.Script(code);
            console.log(`${C.GREEN}  ✓ Syntax check passed${C.RESET}`);

            // Test 2: Isolated execution — whitelisted require only
            const logs = [];
            const sandbox = {
                console: { log: (...a) => logs.push(a.join(' ')), error: () => {}, warn: () => {} },
                setTimeout: () => {}, setInterval: () => {}, clearTimeout: () => {}, clearInterval: () => {},
                Math, JSON, Array, Object, String, Number, Boolean, Date, Error, Map, Set, Promise, RegExp,
                Buffer,
                require: (mod) => {
                    if (CONFIG.SANDBOX_SAFE_MODULES.has(mod)) return require(mod);
                    throw new Error(`Module '${mod}' not allowed in sandbox`);
                },
                __dirname: '/tmp/pika-sandbox',
                __filename: '/tmp/pika-sandbox/test.js',
                process: { env: {}, argv: [], version: process.version, platform: process.platform },
                module: { exports: {} },
                exports: {}
            };

            const ctx = vm.createContext(sandbox);
            const script = new vm.Script(code, { filename: 'pika-mutation-test.js' });
            script.runInContext(ctx, { timeout: CONFIG.RUNTIME_TIMEOUT, displayErrors: true });

            console.log(`${C.GREEN}  ✓ Isolated execution test passed${C.RESET}`);

            return { valid: true, message: 'All validation tests passed', output: logs.join('\n') || null };

        } catch (error) {
            const isTimeout = error.message.includes('Script execution timed out');
            return {
                valid: false,
                message: isTimeout ? `Timed out after ${CONFIG.RUNTIME_TIMEOUT}ms` : error.message,
                stack: error.stack
            };
        }
    }

    // ══════════════════════════════════════════════════════════════════════
    // 🧬 MUTATION PIPELINE — FIXED: validate BEFORE write, not after
    // ══════════════════════════════════════════════════════════════════════
    async mutate(targetFile, newCode, options = {}) {
        const startTime = Date.now();

        // 🔒 NEW: acquire shared lock first — nobody else should be mutating
        const gotLock = await this.acquireLock('mutation_service');
        if (!gotLock) {
            return { success: false, reason: 'LOCK_UNAVAILABLE', message: 'Another mutation system is currently active' };
        }

        this.metrics.totalMutations++;

        console.log(`\n${C.PURPLE}${C.BOLD}╔════════════════════════════════════════╗${C.RESET}`);
        console.log(`${C.PURPLE}${C.BOLD}║   MUTATION ENGINE v3.0 - INITIATED    ║${C.RESET}`);
        console.log(`${C.PURPLE}${C.BOLD}╚════════════════════════════════════════╝${C.RESET}`);
        console.log(`${C.CYAN}Target:${C.RESET} ${targetFile}`);
        console.log(`${C.CYAN}Time:${C.RESET} ${new Date().toISOString()}`);

        const fullPath = path.join(BASE_DIR, targetFile);
        let oldCode = null, oldHash = null, backupPath = null;

        try {
            // STEP 1: Security check
            const securityCheck = this.isSafeToEdit(targetFile);
            if (!securityCheck.safe) {
                this.metrics.rejected++;
                await this.releaseLock();
                return { success: false, reason: 'SECURITY_BLOCK', message: securityCheck.reason };
            }

            // STEP 2: Read existing code (no write yet)
            if (await fs.pathExists(fullPath)) {
                const brainData = await this.readBrain(targetFile);
                oldCode = brainData.code;
                oldHash = brainData.hash;
                console.log(`${C.BLUE}[BRAIN READ]${C.RESET} ${brainData.lines} lines, ${(brainData.size / 1024).toFixed(2)}KB`);
            }

            // STEP 3: Diff analysis (in-memory only, no disk touched)
            const diffAnalysis = await this.analyzeDiff(oldCode, newCode, targetFile);

            if (!diffAnalysis.valid) {
                console.log(`${C.YELLOW}[REJECTED]${C.RESET} ${diffAnalysis.reason}`);
                this.metrics.rejected++;
                await this.logToVault(targetFile, "REJECTED", { reason: diffAnalysis.reason, severity: diffAnalysis.severity, metrics: diffAnalysis.metrics });
                try { trackAction("MUTATION_REJECTED", targetFile, diffAnalysis.reason); } catch (e) {}
                await this.releaseLock();
                return { success: false, reason: 'VALIDATION_FAILED', message: diffAnalysis.reason, analysis: diffAnalysis };
            }

            if (diffAnalysis.warnings && diffAnalysis.warnings.length > 0) {
                console.log(`${C.YELLOW}[WARNINGS]${C.RESET}`);
                diffAnalysis.warnings.forEach(w => console.log(`  ${C.YELLOW}⚠${C.RESET} ${w}`));
            }

            console.log(`${C.GREEN}[DIFF ANALYSIS]${C.RESET} ${diffAnalysis.reason}`);

            // ★★★ THE KEY FIX ★★★
            // STEP 4 (moved up, was Step 5): sandbox-validate the NEW CODE
            // AS A STRING — before it ever touches the filesystem.
            if (fullPath.endsWith('.js') || fullPath.endsWith('.ts')) {
                const validation = this.validateInSandbox(newCode);
                if (!validation.valid) {
                    console.log(`${C.RED}[VALIDATION FAILED]${C.RESET} ${validation.message}`);
                    this.metrics.rejected++;
                    await this.logToVault(targetFile, "REJECTED_SANDBOX", { reason: validation.message });
                    try { trackAction("MUTATION_SANDBOX_REJECTED", targetFile, validation.message); } catch (e) {}
                    await this.releaseLock();
                    // Nothing was ever written — no rollback needed
                    return { success: false, reason: 'SANDBOX_VALIDATION_FAILED', message: validation.message };
                }
            }

            // STEP 5: ONLY NOW do we back up and write — code is proven safe first
            if (oldCode !== null) {
                backupPath = await this.createBackup(targetFile, oldCode);
                console.log(`${C.BLUE}[BACKUP]${C.RESET} Secured at: ${path.basename(backupPath)}`);
            }

            await fs.writeFile(fullPath, newCode, 'utf8');
            console.log(`${C.CYAN}[INJECTION]${C.RESET} New code written to filesystem (post-validation)`);

            // STEP 6: Success bookkeeping
            const newHash = this.hashCode(newCode);
            const duration = Date.now() - startTime;

            console.log(`${C.GREEN}${C.BOLD}[SUCCESS]${C.RESET} Mutation completed in ${duration}ms 🚀\n`);

            this.metrics.successful++;
            this.mutationHistory.set(targetFile, { lastMutation: new Date().toISOString(), oldHash, newHash, success: true });

            await this.saveMetrics();
            await this.logToVault(targetFile, "SUCCESS", { oldHash, newHash, duration, metrics: diffAnalysis.metrics });
            try { trackAction("MUTATION_SUCCESS", targetFile, `Completed in ${duration}ms`); } catch (e) {}

            await this.releaseLock();
            return { success: true, message: `Successfully mutated ${targetFile}`, hash: newHash, duration, backupPath, metrics: diffAnalysis.metrics };

        } catch (error) {
            // STEP 7: Rollback — only relevant now if writeFile itself threw,
            // since validation already happened pre-write
            console.log(`\n${C.RED}${C.BOLD}[ERROR DETECTED]${C.RESET} ${error.message}`);
            this.metrics.rollbacks++;

            try {
                if (oldCode !== null && await fs.pathExists(fullPath)) {
                    await fs.writeFile(fullPath, oldCode, 'utf8');
                    console.log(`${C.GREEN}[ROLLBACK SUCCESS]${C.RESET} File restored to previous state 🛡️\n`);
                }

                await this.logToVault(targetFile, "ROLLED_BACK", { error: error.message, stack: error.stack, oldHash });
                try { trackAction("MUTATION_ROLLBACK", targetFile, error.message); } catch (e) {}

                await this.releaseLock();
                return { success: false, reason: 'ROLLBACK_EXECUTED', message: error.message, rolledBack: true, backupPath };

            } catch (rollbackError) {
                console.error(`${C.RED}${C.BOLD}[CRITICAL]${C.RESET} Rollback failed: ${rollbackError.message}`);
                this.metrics.failed++;
                await this.releaseLock();
                return { success: false, reason: 'CRITICAL_FAILURE', message: 'Both mutation and rollback failed', error: error.message, rollbackError: rollbackError.message };
            }
        }
    }

    // ==========================================
    // 📊 METRICS PERSISTENCE (unchanged)
    // ==========================================
    async saveMetrics() {
        try {
            const data = { metrics: this.metrics, history: Object.fromEntries(this.mutationHistory), lastUpdated: new Date().toISOString() };
            await fs.writeJson(MUTATION_HISTORY, data, { spaces: 2 });
        } catch (error) {
            console.error(`${C.RED}[METRICS ERROR]${C.RESET} ${error.message}`);
        }
    }

    getMetrics() {
        return {
            ...this.metrics,
            successRate: this.metrics.totalMutations > 0
                ? ((this.metrics.successful / this.metrics.totalMutations) * 100).toFixed(2) + '%'
                : 'N/A'
        };
    }

    getHistory(targetFile = null) {
        if (targetFile) return this.mutationHistory.get(targetFile) || null;
        return Object.fromEntries(this.mutationHistory);
    }

    async restoreFromBackup(targetFile, backupName = null) {
        try {
            const fileName = path.basename(targetFile);
            const fullPath = path.join(BASE_DIR, targetFile);

            let backupPath;
            if (backupName) {
                backupPath = path.join(BACKUP_DIR, backupName);
            } else {
                const allBackups = await fs.readdir(BACKUP_DIR);
                const fileBackups = allBackups
                    .filter(f => f.startsWith(fileName))
                    .map(f => ({ name: f, path: path.join(BACKUP_DIR, f), time: fs.statSync(path.join(BACKUP_DIR, f)).mtime }))
                    .sort((a, b) => b.time - a.time);

                if (fileBackups.length === 0) throw new Error('No backups found');
                backupPath = fileBackups[0].path;
            }

            const backupCode = await fs.readFile(backupPath, 'utf8');
            await fs.writeFile(fullPath, backupCode, 'utf8');
            console.log(`${C.GREEN}[RESTORE SUCCESS]${C.RESET} Restored from ${path.basename(backupPath)}`);

            return { success: true, backupPath: path.basename(backupPath) };
        } catch (error) {
            console.error(`${C.RED}[RESTORE ERROR]${C.RESET} ${error.message}`);
            return { success: false, error: error.message };
        }
    }
}

// ==========================================
// EXPORTS
// ==========================================
const mutationEngine = new MutationEngine();

module.exports = mutationEngine;
module.exports.MutationEngine = MutationEngine;
module.exports.CONFIG = CONFIG;
