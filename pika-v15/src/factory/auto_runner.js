const { spawn } = require('child_process');
const path = require('path');

const MAX_RETRIES = 3;

// Exact venv python path use karenge taaki pathing issues na aayen
const PYTHON_EXEC = path.resolve(__dirname, '../../venv/bin/python');

function extractFunctionName(errorLog) {
    const regex = /in\s+([a-zA-Z0-9_]+)/g;
    let match;
    let matches = [];
    while ((match = regex.exec(errorLog)) !== null) {
        matches.push(match[1]);
    }
    return matches.length > 0 ? matches[matches.length - 1] : "unknown";
}

async function triggerAutoFix(filePath, errorLog) {
    console.log(`\n[Auto-Runner] 🚨 Crash Detected! Analyzing stack trace...`);

    const funcName = extractFunctionName(errorLog);

    if (funcName === "unknown" || funcName === "<module>") {
        console.log("[Auto-Runner] ⚠️ Could not extract exact function name. Pika might need manual AST targeting.");
        return { success: false, neuronId: null };
    }

    console.log(`[Auto-Runner] 🎯 Target Function Identified: '${funcName}'. Sending telemetry to Pika Brain...`);

    try {
        const response = await fetch('http://localhost:3000/api/fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_path: filePath,
                function_name: funcName,
                error_log: errorLog
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            console.log(`[Auto-Runner] 🛠️ Pika Brain applied fix. (neuron: ${data.neuron_id || 'n/a'}, from_api: ${data.used_api})`);
            return { success: true, neuronId: data.neuron_id || null };
        } else {
            console.error(`[Auto-Runner] ❌ Pika failed to fix:`, data);
            return { success: false, neuronId: null };
        }
    } catch (err) {
        console.error(`\n[Auto-Runner] ❌ Connection Error: Is Pika's Express Server running on port 3000?`, err.message);
        return { success: false, neuronId: null };
    }
}

// NEW: closes the feedback loop — tells Pika's brain whether the neuron it
// used/created actually resolved the crash on re-run.
async function reportOutcome(neuronId, success) {
    if (!neuronId) return;
    try {
        await fetch('http://localhost:3000/api/outcome', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ neuron_id: neuronId, success })
        });
        console.log(`[Auto-Runner] 📡 Reported outcome to Pika Brain: neuron ${neuronId} -> ${success ? 'SUCCESS' : 'FAILED'}`);
    } catch (err) {
        console.error(`[Auto-Runner] ⚠️ Could not report outcome (brain will not learn from this run):`, err.message);
    }
}

function runAndHeal(filePath, attempt = 1, pendingNeuronId = null) {
    if (attempt > MAX_RETRIES) {
        console.log(`\n[Auto-Runner] 🛑 MAX RETRIES REACHED (${MAX_RETRIES}). Mission Aborted.\n`);
        // We never confirmed the last fix worked — tell the brain it failed.
        reportOutcome(pendingNeuronId, false);
        return;
    }

    console.log(`\n==================================================`);
    console.log(`▶️ EXECUTION ATTEMPT ${attempt}/${MAX_RETRIES} | Target: ${path.basename(filePath)}`);
    console.log(`==================================================`);

    const proc = spawn(PYTHON_EXEC, [filePath]);
    let errorLog = "";

    proc.on('error', (err) => {
        console.error(`[Auto-Runner] Spawn Error:`, err.message);
    });

    proc.stdout.on('error', () => {});
    proc.stderr.on('error', () => {});

    proc.stdout.on('data', (data) => {
        process.stdout.write(data.toString());
    });

    proc.stderr.on('data', (data) => {
        errorLog += data.toString();
        process.stdout.write(data.toString());
    });

    proc.on('close', async (code) => {
        if (code === 0) {
            console.log(`\n[Auto-Runner] ✅ EXECUTION SUCCESSFUL! Zero errors detected. Pika rests.\n`);
            // If this success came right after a fix was applied, confirm it worked.
            await reportOutcome(pendingNeuronId, true);
        } else {
            console.log(`\n[Auto-Runner] 💥 Execution Failed (Exit Code: ${code}). Initiating Self-Healing Protocol...`);

            // If a previous fix's neuron was pending and the crash happened again,
            // that neuron's fix did NOT actually work — report failure before trying a new one.
            if (pendingNeuronId) {
                await reportOutcome(pendingNeuronId, false);
            }

            const { success: isHealed, neuronId } = await triggerAutoFix(filePath, errorLog);

            if (isHealed) {
                console.log(`[Auto-Runner] 🔄 Restarting execution loop in 2 seconds...`);
                setTimeout(() => runAndHeal(filePath, attempt + 1, neuronId), 2000);
            } else {
                console.log(`[Auto-Runner] 💀 Auto-Heal failed. Stopping loop.`);
            }
        }
    });
}

const targetFile = process.argv[2];
if (!targetFile) {
    console.log("Usage: node src/factory/auto_runner.js <absolute_path_to_python_file>");
    process.exit(1);
}

runAndHeal(path.resolve(targetFile));
