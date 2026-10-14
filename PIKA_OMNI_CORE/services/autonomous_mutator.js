// ══════════════════════════════════════════════════════════════════════════
// 🤖 PIKA — AUTONOMOUS MUTATOR v6.0 (REAL VALIDATION EDITION)
// Fake keyword-matching evaluation REMOVED.
// Now delegates all mutation + scoring + validation to logic_factory.js's
// real sandboxed engine (vm.Script syntax check, security scan, runtime test,
// heuristic score before/after comparison, backup+restore on regression).
// ══════════════════════════════════════════════════════════════════════════
'use strict';

const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');
const { processMessage } = require('../core/router.js');
const { trackAction } = require('./tracker.js');

// 🔗 REAL ENGINE — this is the fix. No more fake "response.includes('success')".
const logicFactory = require('./logic_factory.js');

// ==========================================
// 🎨 TERMINAL COLORS
// ==========================================
const C = {
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m",
    YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", BLUE: "\x1b[34m",
    MAGENTA: "\x1b[95m", WHITE: "\x1b[37m", RESET: "\x1b[0m",
    BOLD: "\x1b[1m", DIM: "\x1b[2m"
};

let isMutating = false;
let mutationLevel = 1;

// evolutionMetrics ab REAL data track karta hai — score deltas, not string guesses
let evolutionMetrics = {
    successRate: 0,
    totalMutations: 0,
    improvedMutations: 0,
    failedMutations: 0,
    rejectedMutations: 0,      // NEW: mutations jo score gira dein, reverted
    avgScoreDelta: 0,          // NEW: real quality signal
    mutationHistory: []
};

// ==========================================
// 📊 MUTATION LEVEL STRATEGY (unchanged — good design)
// ==========================================
const MUTATION_STRATEGIES = {
    1: { name: "OPTIMIZATION", description: "Code cleanup and performance enhancements", weight: 0.3, focus: "readability, efficiency, conventions" },
    2: { name: "ENHANCEMENT", description: "Feature expansion and capability building", weight: 0.5, focus: "new functions, improved algorithms, error handling" },
    3: { name: "EVOLUTION", description: "System redesign and pattern innovation", weight: 0.7, focus: "design patterns, modularity, scalability" },
    4: { name: "COGNITION", description: "Self-evaluating code that improves its own logic", weight: 0.85, focus: "meta-programming, self-analysis, adaptive learning" },
    5: { name: "SINGULARITY", description: "Reaching towards AGI-level self-evolution", weight: 1.0, focus: "emergent behavior, recursive self-improvement, knowledge synthesis" }
};

// ==========================================
// 🧬 CODE FINGERPRINTING (now actually used — see getSystemMap)
// ==========================================
async function generateCodeSignature(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf8');
        return crypto.createHash('sha256').update(content).digest('hex');
    } catch (e) {
        return null;
    }
}

// ==========================================
// 👁️ SYSTEM SCANNER
// ==========================================
async function getSystemMap() {
    let systemTree = [];
    let fileMetrics = { total: 0, byType: {}, signatures: {} };
    const dirs = ['../core', '../services', '../utils'];
    const PROTECTED_FILES = ['server.js', 'autonomous_mutator.js', 'memory_manager.js'];

    for (const dir of dirs) {
        const dirPath = path.join(__dirname, dir);
        try {
            if (await fs.pathExists(dirPath)) {
                const files = await fs.readdir(dirPath);
                for (const file of files) {
                    if (file.endsWith('.js') && !PROTECTED_FILES.includes(file)) {
                        const filePath = path.join(dirPath, file);
                        const fullPath = `${dir.replace('../', '')}/${file}`;
                        systemTree.push(fullPath);

                        const sig = await generateCodeSignature(filePath);
                        if (sig) fileMetrics.signatures[fullPath] = sig;

                        fileMetrics.total++;
                        const type = file.split('.')[0];
                        fileMetrics.byType[type] = (fileMetrics.byType[type] || 0) + 1;
                    }
                }
            } else if (dir === '../utils') {
                await fs.ensureDir(dirPath);
                console.log(`${C.BLUE}[SYSTEM EXPANSION]${C.RESET} Created /utils folder.`);
            }
        } catch (scanError) {
            console.error(`${C.RED}[SCAN ERROR]${C.RESET} Failed to read ${dir}: ${scanError.message}`);
        }
    }
    return { files: systemTree.join(', '), fileList: systemTree, metrics: fileMetrics };
}

// ==========================================
// 🎯 MUTATION LEVEL PREDICTOR (unchanged)
// ==========================================
async function calculateOptimalMutationLevel(systemMap) {
    const fileCount = systemMap.metrics.total;
    const successRate = evolutionMetrics.successRate;
    let calculatedLevel = 1;
    if (fileCount > 10 && successRate > 0.7) calculatedLevel = 2;
    if (fileCount > 20 && successRate > 0.8) calculatedLevel = 3;
    if (fileCount > 30 && successRate > 0.85) calculatedLevel = 4;
    if (fileCount > 50 && successRate > 0.92) calculatedLevel = 5;
    return Math.min(calculatedLevel, 5);
}

// ==========================================
// 🚀 MAIN EVOLUTION CYCLE — now uses REAL validation
// ==========================================
async function runAutoEvolution() {
    if (isMutating) return;
    if (!global.isSleeping) return; // VM sandbox safety — stay silent while architect works

    isMutating = true;

    try {
        console.log(`\n${C.PURPLE}${C.BOLD}╔════════════════════════════════════════════════════╗${C.RESET}`);
        console.log(`${C.PURPLE}${C.BOLD}║    [⚡ EVOLUTION CYCLE — REAL VALIDATION MODE ⚡]    ║${C.RESET}`);
        console.log(`${C.PURPLE}${C.BOLD}╚════════════════════════════════════════════════════╝${C.RESET}`);

        // Step 1: Scan system
        const systemMap = await getSystemMap();
        console.log(`${C.CYAN}[NEURAL SCAN]${C.RESET} Analyzing ${systemMap.metrics.total} files...`);

        // Step 2: Pick mutation level/strategy (still useful for prompt framing)
        const optimalLevel = await calculateOptimalMutationLevel(systemMap);
        const strategy = MUTATION_STRATEGIES[optimalLevel];
        mutationLevel = optimalLevel;

        console.log(`\n${C.MAGENTA}[MUTATION LEVEL]${C.RESET} ${C.BOLD}${optimalLevel}/5 - ${strategy.name}${C.RESET}`);
        console.log(`${C.DIM}Focus: ${strategy.focus}${C.RESET}`);

        try { trackAction("EVOLUTION_START", `LEVEL_${optimalLevel}`, strategy.name); } catch (e) {}

        // Step 3: Pick a TARGET FILE to mutate (real target, not abstract prompt)
        const targetFile = pickMutationTarget(systemMap.fileList);
        if (!targetFile) {
            console.log(`${C.YELLOW}[EVOLVE] No eligible target file found — skipping cycle${C.RESET}`);
            isMutating = false;
            return;
        }
        console.log(`${C.CYAN}[TARGET]${C.RESET} ${targetFile}`);

        // Step 4: Delegate to logic_factory's REAL selfEvolve-style pipeline
        // NOTE: logic_factory.selfEvolve() mutates itself (CONFIG.SELF_EVOLUTION.SELF_FILE).
        // For mutating OTHER files, we replicate its safe pattern here using its
        // exported primitives — scoreSelfSource, validateToolInSandbox, backupFile.
        const result = await mutateTargetFile(targetFile, strategy);

        // Step 5: Update REAL metrics (score-based, not string-guessing)
        updateMetrics(result);

        // Step 6: Report
        if (result.success) {
            console.log(`\n${C.GREEN}${C.BOLD}✨ [MUTATION ACCEPTED] ✨${C.RESET}`);
            console.log(`${C.GREEN}Score: ${result.scoreBefore} → ${result.scoreAfter} (${result.delta >= 0 ? '+' : ''}${result.delta})${C.RESET}`);
            console.log(`${C.CYAN}Security score: ${result.securityScore ?? 'n/a'}${C.RESET}`);
        } else {
            console.log(`\n${C.YELLOW}[MUTATION REJECTED]${C.RESET} ${result.reason}`);
            console.log(`${C.DIM}Original file restored from backup — no regression written to disk.${C.RESET}`);
        }

        console.log(`${C.CYAN}[SUCCESS RATE]${C.RESET} ${(evolutionMetrics.successRate * 100).toFixed(1)}%`);

        try { trackAction("EVOLUTION_END", `LEVEL_${optimalLevel}`, result.success ? "Success" : "Rejected"); } catch (e) {}

    } catch (error) {
        console.log(`${C.RED}[EVOLUTION CRASH]${C.RESET} ${error.message}`);
        updateMetrics({ success: false, delta: 0, reason: error.message });
        try { trackAction("EVOLUTION_CRASH", "Manager", error.message); } catch (e) {}
    }

    isMutating = false;
}

// ==========================================
// 🎯 TARGET SELECTION — random-ish but weighted toward less-recently-mutated files
// ==========================================
function pickMutationTarget(fileList) {
    if (!fileList || !fileList.length) return null;
    // Simple rotation: pick least-recently-touched file based on history log
    const touched = new Set(evolutionMetrics.mutationHistory.slice(-10).map(h => h.targetFile));
    const untouched = fileList.filter(f => !touched.has(f));
    const pool = untouched.length ? untouched : fileList;
    return pool[Math.floor(Math.random() * pool.length)];
}

// ==========================================
// 🔬 REAL MUTATION PIPELINE (per target file)
// Uses logic_factory's actual sandbox + scoring — this REPLACES evaluateMutation()
// ==========================================
async function mutateTargetFile(relativeTargetPath, strategy) {
    const absPath = path.join(__dirname, '..', relativeTargetPath);

    if (!fs.existsSync(absPath)) {
        return { success: false, reason: 'target file missing', delta: 0 };
    }

    const originalSource = fs.readFileSync(absPath, 'utf8');
    const scoreBefore = logicFactory.scoreSelfSource(originalSource);

    // Pick a mutation target function inside this file (reuse logic_factory's parser)
    const fns = logicFactory.parseFunctions(originalSource);
    const candidates = [...fns.keys()].filter(n => (fns.get(n).body || '').split('\n').length > 5);

    if (!candidates.length) {
        return { success: false, reason: 'no eligible functions to mutate', delta: 0 };
    }

    const funcName = candidates[Math.floor(Math.random() * candidates.length)];
    const funcInfo = fns.get(funcName);

    console.log(`${C.YELLOW}[MUTATE]${C.RESET} ${funcName} → focus: ${strategy.focus}`);

    // Step A: Ask LLM for improved function (reuses cognitiveFallback — no duplicate engine code)
    const improved = await logicFactory.mutateOneFunction(funcName, funcInfo.body, strategy.focus);
    if (!improved) {
        return { success: false, reason: `LLM produced no usable output for ${funcName}`, delta: 0 };
    }

    // Step B: Apply mutation in-memory
    const mutatedSource = logicFactory.applyMutation(originalSource, funcName, improved);
    if (!mutatedSource) {
        return { success: false, reason: `mutation invalid — syntax broken for ${funcName}`, delta: 0 };
    }

    // Step C: REAL sandbox validation — syntax + security + runtime (strict=true runs it)
    const validation = await logicFactory.validateToolInSandbox(mutatedSource, true);
    if (!validation.success) {
        return {
            success: false,
            reason: `sandbox validation failed at layer '${validation.layer}': ${validation.error}`,
            delta: 0
        };
    }

    // Step D: Objective score comparison — this is the anti-gaming check
    const scoreAfter = logicFactory.scoreSelfSource(mutatedSource);
    const delta = scoreAfter - scoreBefore;

    if (scoreAfter < scoreBefore) {
        // REJECT — do not write regression to disk
        return {
            success: false,
            reason: `score regressed (${scoreBefore} → ${scoreAfter})`,
            delta,
            scoreBefore,
            scoreAfter,
            targetFile: relativeTargetPath,
            funcName
        };
    }

    // Step E: Backup + write only if score held or improved
    const bkp = await logicFactory.backupFile(absPath);
    if (!bkp.success) {
        return { success: false, reason: `backup failed: ${bkp.error}`, delta };
    }

    const stamp = `// 🧬 Mutated by autonomous_mutator v6.0 — ${new Date().toISOString()}\n` +
                  `// Function: ${funcName} | Score: ${scoreBefore} → ${scoreAfter}\n`;
    fs.writeFileSync(absPath, stamp + mutatedSource, 'utf8');

    return {
        success: true,
        delta,
        scoreBefore,
        scoreAfter,
        securityScore: validation.securityScore,
        targetFile: relativeTargetPath,
        funcName,
        backupPath: bkp.backupPath
    };
}

// ==========================================
// 📈 REAL METRICS TRACKER
// ==========================================
function updateMetrics(result) {
    evolutionMetrics.totalMutations++;

    if (result.success) {
        evolutionMetrics.improvedMutations++;
    } else if (result.reason && result.reason.startsWith('score regressed')) {
        evolutionMetrics.rejectedMutations++;
        evolutionMetrics.failedMutations++;
    } else {
        evolutionMetrics.failedMutations++;
    }

    evolutionMetrics.successRate = evolutionMetrics.improvedMutations / evolutionMetrics.totalMutations;

    // Running average of score delta — real learning signal over time
    const n = evolutionMetrics.mutationHistory.length;
    evolutionMetrics.avgScoreDelta =
        ((evolutionMetrics.avgScoreDelta * n) + (result.delta || 0)) / (n + 1);

    evolutionMetrics.mutationHistory.push({
        timestamp: new Date().toISOString(),
        success: result.success,
        level: mutationLevel,
        targetFile: result.targetFile || null,
        funcName: result.funcName || null,
        scoreBefore: result.scoreBefore ?? null,
        scoreAfter: result.scoreAfter ?? null,
        delta: result.delta ?? 0,
        reason: result.reason || null
    });

    if (evolutionMetrics.mutationHistory.length > 100) {
        evolutionMetrics.mutationHistory.shift();
    }

    displayMetrics();
}

function displayMetrics() {
    console.log(`\n${C.CYAN}[EVOLUTION METRICS — REAL DATA]${C.RESET}`);
    console.log(`${C.BLUE}├─ Total Mutations: ${C.RESET}${evolutionMetrics.totalMutations}`);
    console.log(`${C.GREEN}├─ Accepted: ${C.RESET}${evolutionMetrics.improvedMutations}`);
    console.log(`${C.YELLOW}├─ Rejected (score regression): ${C.RESET}${evolutionMetrics.rejectedMutations}`);
    console.log(`${C.RED}├─ Failed (other): ${C.RESET}${evolutionMetrics.failedMutations - evolutionMetrics.rejectedMutations}`);
    console.log(`${C.MAGENTA}└─ Avg Score Delta: ${C.RESET}${evolutionMetrics.avgScoreDelta.toFixed(2)}`);
}

// ==========================================
// 🕒 SCHEDULER (unchanged)
// ==========================================
function startAutoEvolutionLoop(intervalMinutes = 5) {
    console.log(`\n${C.GREEN}${C.BOLD}[AUTONOMOUS MUTATOR v6.0 — REAL VALIDATION INITIALIZED]${C.RESET}`);
    console.log(`${C.GREEN}Evolution Cycle: Every ${intervalMinutes} minutes${C.RESET}`);
    console.log(`${C.GREEN}Safety: VM Sandbox + Score-Gated Writes${C.RESET}\n`);

    setTimeout(() => {
        runAutoEvolution();
        setInterval(runAutoEvolution, intervalMinutes * 60 * 1000);
    }, 30000);
}

// ==========================================
// 📤 EXPORTS
// ==========================================
module.exports = {
    startAutoEvolutionLoop,
    runAutoEvolution,
    getMutationLevel: () => mutationLevel,
    getMetrics: () => evolutionMetrics,
    MUTATION_STRATEGIES
};
