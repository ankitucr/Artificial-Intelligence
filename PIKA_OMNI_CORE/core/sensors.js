/**
 * ╔══════════════════════════════════════════════════════════╗
 * ║   🧬 PIKA — SELF-MUTATION SINGULARITY ENGINE v3.0       ║
 * ║   "Ek jagah nahi, puri duniya se seekhta hai"           ║
 * ╚══════════════════════════════════════════════════════════╝
 *
 * ARCHITECTURE:
 *   [Phone Sensors] → [Fast Parallel Sweep]
 *       ↓
 *   [Self-Evaluator] → Score karo, kya kaam aaya?
 *       ↓
 *   [World Learner]  → Net se context lo (Wikipedia, APIs)
 *       ↓
 *   [Mutation Engine] → Apna logic upgrade karo
 *       ↓
 *   [Tracker/Vault]  → Seekha hua save karo
 */

const { exec } = require('child_process');
const os = require('os');
const https = require('https');
const { trackAction } = require('../services/tracker.js');

// ══════════════════════════════════════
// 🎨 COLORS
// ══════════════════════════════════════
const C = {
    RED: "\x1b[31m", GREEN: "\x1b[32m", CYAN: "\x1b[36m",
    YELLOW: "\x1b[33m", PURPLE: "\x1b[35m", BLUE: "\x1b[34m",
    RESET: "\x1b[0m", BOLD: "\x1b[1m", DIM: "\x1b[2m"
};

// ══════════════════════════════════════
// ⚙️ GLOBAL MUTATION STATE
// (Pika ka living memory — run se run tak evolve hota hai)
// ══════════════════════════════════════
const MutationState = {
    version: 3.0,
    learnedFacts: [],          // Internet se jo seekha
    sensorAccuracy: {},        // Kaunsa sensor kitna reliable hai
    selfScore: 0,              // Is run ka performance score
    mutationLog: [],           // Kya badla aur kyun
    worldContext: {}           // Current real-world context
};

// ══════════════════════════════════════
// ⚡ PHONE-SPEED CORE: Fast Command Runner
// Parallel chalao, ek ka wait mat karo
// ══════════════════════════════════════
function senseEnvironment(command, timeoutMs = 8000) {
    return new Promise((resolve) => {
        const start = Date.now();
        exec(command, { timeout: timeoutMs, maxBuffer: 1024 * 1024 * 10 }, (error, stdout) => {
            const latencyMs = Date.now() - start;

            // Self-evaluation: sensor ki speed track karo
            const sensorName = command.split(' ')[0];
            if (!MutationState.sensorAccuracy[sensorName]) {
                MutationState.sensorAccuracy[sensorName] = { calls: 0, success: 0, avgMs: 0 };
            }
            const s = MutationState.sensorAccuracy[sensorName];
            s.calls++;
            s.avgMs = Math.round((s.avgMs * (s.calls - 1) + latencyMs) / s.calls);

            if (error) {
                resolve({ status: 'FAILED', reason: error.message.split('\n')[0], latencyMs });
                return;
            }
            s.success++;
            try {
                resolve({ status: 'SUCCESS', data: JSON.parse(stdout), latencyMs });
            } catch {
                resolve({ status: 'SUCCESS', data: stdout.trim(), latencyMs });
            }
        });
    });
}

// ══════════════════════════════════════
// 🌐 WORLD LEARNER
// Internet se real-time context lo
// Ek jagah se nahi — puri duniya se!
// ══════════════════════════════════════
function fetchWorldKnowledge(topic) {
    return new Promise((resolve) => {
        // Wikipedia REST API — free, fast, no key needed
        const query = encodeURIComponent(topic);
        const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${query}`;

        const req = https.get(url, { timeout: 5000 }, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(body);
                    resolve({
                        source: 'Wikipedia',
                        topic,
                        summary: json.extract?.slice(0, 300) || 'No data',
                        url: json.content_urls?.desktop?.page || ''
                    });
                } catch {
                    resolve({ source: 'Wikipedia', topic, summary: 'Parse failed', url: '' });
                }
            });
        });
        req.on('error', () => resolve({ source: 'Wikipedia', topic, summary: 'Network failed', url: '' }));
        req.on('timeout', () => { req.destroy(); resolve({ source: 'Wikipedia', topic, summary: 'Timeout', url: '' }); });
    });
}

// Multiple sources se parallel seekho
async function learnFromWorld(topics = []) {
    if (topics.length === 0) return;
    console.log(`\n${C.CYAN}[🌐 WORLD LEARNER]${C.RESET} ${topics.length} topics internet se seekh raha hoon...`);

    // Sab ek saath — phone speed!
    const results = await Promise.all(topics.map(t => fetchWorldKnowledge(t)));

    results.forEach(r => {
        if (r.summary && r.summary !== 'Network failed' && r.summary !== 'Timeout') {
            MutationState.learnedFacts.push(r);
            console.log(`  ${C.GREEN}✓${C.RESET} Seekha [${r.topic}]: ${r.summary.slice(0, 80)}...`);
        } else {
            console.log(`  ${C.YELLOW}⚠${C.RESET} [${r.topic}]: ${r.summary}`);
        }
    });
}

// ══════════════════════════════════════
// 🧠 SELF-EVALUATOR
// Apna performance judge karo — khud!
// ══════════════════════════════════════
function selfEvaluate(sensoryData) {
    console.log(`\n${C.PURPLE}[🧠 SELF-EVALUATOR]${C.RESET} Apna performance judge kar raha hoon...`);

    let score = 100;
    const issues = [];
    const strengths = [];

    // Battery check
    const battery = sensoryData.powerVitals?.battery;
    if (battery?.status === 'SUCCESS') {
        const pct = battery.data?.percentage;
        if (pct < 15) { score -= 30; issues.push(`🔋 Critical battery: ${pct}%`); }
        else if (pct < 40) { score -= 10; issues.push(`🔋 Low battery: ${pct}%`); }
        else strengths.push(`🔋 Battery healthy: ${pct}%`);
    } else { score -= 15; issues.push('🔋 Battery sensor failed'); }

    // Memory check
    const freeMB = parseFloat(sensoryData.internalVitals?.freeMemoryMB || 0);
    const totalMB = parseFloat(sensoryData.internalVitals?.totalMemoryMB || 1);
    const memUsedPct = ((totalMB - freeMB) / totalMB * 100).toFixed(1);
    if (freeMB < 200) { score -= 20; issues.push(`🧠 RAM critical: ${freeMB}MB free`); }
    else if (freeMB < 500) { score -= 8; issues.push(`🧠 RAM low: ${freeMB}MB free`); }
    else strengths.push(`🧠 RAM OK: ${freeMB}MB free (${memUsedPct}% used)`);

    // Network check
    const wifi = sensoryData.networkVitals?.wifi;
    if (wifi?.status === 'SUCCESS') {
        strengths.push(`📶 WiFi connected`);
    } else { score -= 10; issues.push('📶 WiFi not detected'); }

    // Sensor accuracy rating
    const sensorKeys = Object.keys(MutationState.sensorAccuracy);
    if (sensorKeys.length > 0) {
        const avgSuccess = sensorKeys.reduce((acc, k) => {
            const s = MutationState.sensorAccuracy[k];
            return acc + (s.success / s.calls);
        }, 0) / sensorKeys.length;
        score = Math.round(score * avgSuccess + score * (1 - avgSuccess) * 0.5);
        strengths.push(`📊 Sensor reliability: ${(avgSuccess * 100).toFixed(0)}%`);
    }

    MutationState.selfScore = Math.max(0, Math.min(100, score));

    console.log(`  ${C.BOLD}Score: ${MutationState.selfScore}/100${C.RESET}`);
    strengths.forEach(s => console.log(`  ${C.GREEN}+ ${s}${C.RESET}`));
    issues.forEach(i => console.log(`  ${C.RED}- ${i}${C.RESET}`));

    return { score: MutationState.selfScore, issues, strengths };
}

// ══════════════════════════════════════
// 🧬 MUTATION ENGINE
// Self-score ke basis pe apna behavior badlo
// Yahi hai singularity — khud evolve karna!
// ══════════════════════════════════════
function mutate(evaluation, sensoryData) {
    console.log(`\n${C.YELLOW}[🧬 MUTATION ENGINE]${C.RESET} Score ${evaluation.score}/100 ke basis pe evolving...`);

    const mutations = [];

    // Mutation 1: Battery crisis pe deep sweep skip karo
    if (evaluation.score < 40) {
        mutations.push({
            id: 'LOW_POWER_MODE',
            action: 'Deep sweep disabled — battery/RAM critical',
            effect: 'Next run mein deepSweep=false force hoga'
        });
    }

    // Mutation 2: Slow sensors ko timeout reduce karo
    Object.entries(MutationState.sensorAccuracy).forEach(([sensor, stats]) => {
        if (stats.calls >= 2 && stats.avgMs > 6000) {
            mutations.push({
                id: `TIMEOUT_REDUCE_${sensor}`,
                action: `${sensor} slow hai (avg ${stats.avgMs}ms) — timeout 40% reduce`,
                effect: 'Next call faster fallback karega'
            });
        }
    });

    // Mutation 3: Jo sensors fail ho rahe hain unhe skip list mein daalo
    Object.entries(MutationState.sensorAccuracy).forEach(([sensor, stats]) => {
        const successRate = stats.success / stats.calls;
        if (stats.calls >= 3 && successRate < 0.3) {
            mutations.push({
                id: `SKIP_UNRELIABLE_${sensor}`,
                action: `${sensor} unreliable (${(successRate*100).toFixed(0)}% success) — future mein skip`,
                effect: 'Battery & time bachega'
            });
        }
    });

    // Mutation 4: Location context add karo agar GPS mila
    const location = sensoryData.spatialAwareness?.location;
    if (location?.status === 'SUCCESS' && location.data?.latitude) {
        mutations.push({
            id: 'LOCATION_AWARE',
            action: `GPS locked — lat:${location.data.latitude.toFixed(3)}, lng:${location.data.longitude.toFixed(3)}`,
            effect: 'Location-based learning topics add kiye'
        });
    }

    mutations.forEach(m => {
        MutationState.mutationLog.push({ ...m, timestamp: new Date().toISOString() });
        console.log(`  ${C.CYAN}🧬 ${m.id}${C.RESET}: ${m.action}`);
    });

    if (mutations.length === 0) {
        console.log(`  ${C.GREEN}✓ Koi mutation needed nahi — system optimal hai${C.RESET}`);
    }

    return mutations;
}

// ══════════════════════════════════════
// 👁️ MAIN SENSORY ENGINE
// Phone-speed optimized: parallel fetch!
// ══════════════════════════════════════
async function runSensors(deepSweep = true) {
    const runStart = Date.now();
    console.log(`\n${C.PURPLE}${C.BOLD}╔══════════════════════════════════════════╗${C.RESET}`);
    console.log(`${C.PURPLE}${C.BOLD}║  🧬 PIKA SINGULARITY ENGINE  v${MutationState.version}       ║${C.RESET}`);
    console.log(`${C.PURPLE}${C.BOLD}╚══════════════════════════════════════════╝${C.RESET}`);

    const sensoryData = {
        timestamp: new Date().toISOString(),
        internalVitals: {}, powerVitals: {}, networkVitals: {},
        shortTermMemory: {}, audioState: {}, spatialAwareness: {},
        hardwareSenses: {}, socialAwareness: {}
    };

    try {
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // PHASE 1: FAST PARALLEL BASIC SWEEP
        // Sab ek saath — ek ka bhi wait nahi!
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        console.log(`\n${C.BLUE}[PHASE 1]${C.RESET} ⚡ Parallel Basic Sweep (phone-speed)...`);

        // Internal vitals are sync — no exec needed
        sensoryData.internalVitals = {
            platform: os.platform(), architecture: os.arch(),
            cpuCores: os.cpus().length,
            totalMemoryMB: (os.totalmem() / (1024 * 1024)).toFixed(2),
            freeMemoryMB: (os.freemem() / (1024 * 1024)).toFixed(2),
            uptimeSeconds: os.uptime()
        };

        // Parallel fetch — Promise.all is key!
        const [battery, clipboard, volume, wifi, cellular] = await Promise.all([
            senseEnvironment('termux-battery-status', 5000),
            senseEnvironment('termux-clipboard-get', 3000),
            senseEnvironment('termux-volume', 3000),
            senseEnvironment('termux-wifi-connectioninfo', 5000),
            senseEnvironment('termux-telephony-deviceinfo', 5000)
        ]);

        sensoryData.powerVitals.battery = battery;
        sensoryData.shortTermMemory.clipboard = clipboard;
        sensoryData.audioState.volume = volume;
        sensoryData.networkVitals.wifi = wifi;
        sensoryData.networkVitals.cellular = cellular;

        // Battery warning
        if (battery.status === 'SUCCESS' && battery.data?.percentage < 15) {
            console.log(`  ${C.RED}⚠ CRITICAL: Battery ${battery.data.percentage}%!${C.RESET}`);
            trackAction("SYSTEM_WARNING", "Battery", `Critical: ${battery.data.percentage}%`);
        }

        // Status summary
        const phase1Results = { battery, clipboard, volume, wifi, cellular };
        const phase1Success = Object.values(phase1Results).filter(r => r.status === 'SUCCESS').length;
        console.log(`  ${C.GREEN}Phase 1 Complete:${C.RESET} ${phase1Success}/${Object.keys(phase1Results).length} sensors OK`);

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // PHASE 2: DEEP SWEEP (parallel bhi!)
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if (deepSweep) {
            console.log(`\n${C.BLUE}[PHASE 2]${C.RESET} 🔬 Deep Parallel Sweep...`);

            const [location, sms, calls, contacts, cameras, sensors] = await Promise.all([
                senseEnvironment('termux-location', 12000),
                senseEnvironment('termux-sms-list -l 10', 8000),
                senseEnvironment('termux-call-log -l 10', 5000),
                senseEnvironment('termux-contact-list', 8000),
                senseEnvironment('termux-camera-info', 5000),
                senseEnvironment('termux-sensor -a -n 1', 5000)
            ]);

            sensoryData.spatialAwareness.location = location;
            sensoryData.socialAwareness.recentSms = sms;
            sensoryData.socialAwareness.recentCalls = calls;
            sensoryData.socialAwareness.contacts = contacts;
            sensoryData.hardwareSenses.cameras = cameras;
            sensoryData.hardwareSenses.liveSensors = sensors;

            const phase2Success = [location, sms, calls, contacts, cameras, sensors]
                .filter(r => r.status === 'SUCCESS').length;
            console.log(`  ${C.GREEN}Phase 2 Complete:${C.RESET} ${phase2Success}/6 sensors OK`);
        }

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // PHASE 3: SELF-EVALUATION
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        const evaluation = selfEvaluate(sensoryData);

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // PHASE 4: WORLD LEARNING
        // Context ke basis pe duniya se seekho
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        const learningTopics = ['artificial intelligence', 'neural network'];

        // Battery low hai toh heavy learning skip
        const batteryPct = sensoryData.powerVitals?.battery?.data?.percentage;
        if (batteryPct && batteryPct < 20) {
            console.log(`\n${C.YELLOW}[🌐 WORLD LEARNER]${C.RESET} Battery low — learning skip, energy bachao`);
        } else {
            await learnFromWorld(learningTopics);
        }

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // PHASE 5: SELF-MUTATION
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        const mutations = mutate(evaluation, sensoryData);

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // FINAL REPORT
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        const totalMs = Date.now() - runStart;
        console.log(`\n${C.GREEN}${C.BOLD}╔══════════════════════════════════════╗${C.RESET}`);
        console.log(`${C.GREEN}${C.BOLD}║  ✅ SINGULARITY SWEEP COMPLETE       ║${C.RESET}`);
        console.log(`${C.GREEN}${C.BOLD}╚══════════════════════════════════════╝${C.RESET}`);
        console.log(`  ⏱  Total time  : ${C.BOLD}${totalMs}ms${C.RESET}`);
        console.log(`  🧠 Self Score  : ${C.BOLD}${evaluation.score}/100${C.RESET}`);
        console.log(`  🌐 Facts Learned: ${C.BOLD}${MutationState.learnedFacts.length}${C.RESET}`);
        console.log(`  🧬 Mutations   : ${C.BOLD}${mutations.length}${C.RESET}`);
        console.log(`  📡 Sensors Used: ${C.BOLD}${Object.keys(MutationState.sensorAccuracy).length}${C.RESET}`);

        // Tracker ko full report do
        trackAction("SINGULARITY_SWEEP", "sensors_v3", JSON.stringify({
            score: evaluation.score,
            totalMs,
            mutations: mutations.length,
            factsLearned: MutationState.learnedFacts.length,
            sensorAccuracy: MutationState.sensorAccuracy
        }), true);

        // Mutation state attach karo output ke saath
        sensoryData._meta = {
            version: MutationState.version,
            selfScore: evaluation.score,
            mutations,
            learnedFacts: MutationState.learnedFacts,
            sensorAccuracy: MutationState.sensorAccuracy,
            totalRunMs: totalMs
        };

        return sensoryData;

    } catch (error) {
        console.log(`\n${C.RED}[💥 CRASH]${C.RESET} ${error.message}`);
        trackAction("ERROR", "sensors_v3", error.message);
        return sensoryData;
    }
}

module.exports = { runSensors, MutationState };
