const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

const pythonExecutable = path.join(__dirname, '../venv/bin/python');
const bridgeScript = path.join(__dirname, 'python_brain/bridge.py');

// Tracks how many fixes have happened since last brain cleanup
let fixesSinceConsolidation = 0;
const CONSOLIDATE_EVERY_N_FIXES = 10;

// Shared helper: spawn the python bridge with any action payload
function callBridge(payload) {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn(pythonExecutable, [bridgeScript, JSON.stringify(payload)]);
        let finalJsonResponse = "";

        pythonProcess.stderr.on('data', (data) => {
            process.stdout.write(data.toString());
        });

        pythonProcess.stdout.on('data', (data) => {
            finalJsonResponse += data.toString();
        });

        pythonProcess.on('error', (err) => reject(err));

        pythonProcess.on('close', () => {
            try {
                resolve(JSON.parse(finalJsonResponse.trim()));
            } catch (error) {
                reject(new Error(`Bridge communication failed. Raw output: ${finalJsonResponse}`));
            }
        });
    });
}

// Pika's main mutation endpoint
app.post('/api/fix', async (req, res) => {
    const { file_path, function_name, error_log } = req.body;

    if (!file_path || !function_name || !error_log) {
        return res.status(400).json({ error: "Missing required fields (file_path, function_name, error_log)" });
    }

    console.log(`\n[Node.js] 🚀 Waking up Pika Brain to fix: '${function_name}'...`);

    try {
        const result = await callBridge({
            action: "fix_error",
            file_path,
            function_name,
            error_log
        });
        console.log("\n[Node.js] ✅ Task Complete. Sending response to client.");
        res.json(result);
    } catch (error) {
        console.error("\n[Node.js] ❌", error.message);
        res.status(500).json({ status: "error", message: "Bridge communication failed.", detail: error.message });
    }
});

// NEW: report back whether an applied fix actually worked.
// This is what closes the feedback loop and makes Pika reinforcement-learn.
app.post('/api/outcome', async (req, res) => {
    const { neuron_id, success } = req.body;

    if (!neuron_id) {
        return res.status(400).json({ error: "Missing neuron_id" });
    }

    console.log(`\n[Node.js] 📡 Reporting outcome for neuron '${neuron_id}': ${success ? '✅ SUCCESS' : '❌ FAILED'}`);

    try {
        const result = await callBridge({ action: "report_outcome", neuron_id, success });
        res.json(result);

        // Auto-consolidate every N fixes so the brain self-maintains without manual triggering
        fixesSinceConsolidation++;
        if (fixesSinceConsolidation >= CONSOLIDATE_EVERY_N_FIXES) {
            fixesSinceConsolidation = 0;
            console.log(`\n[Node.js] 🧹 Threshold reached (${CONSOLIDATE_EVERY_N_FIXES} fixes) — triggering brain consolidation...`);
            callBridge({ action: "consolidate" })
                .then((r) => console.log("[Node.js] 🧹 Consolidation done:", r))
                .catch((e) => console.error("[Node.js] Consolidation failed:", e.message));
        }
    } catch (error) {
        console.error("\n[Node.js] ❌", error.message);
        res.status(500).json({ status: "error", message: "Bridge communication failed.", detail: error.message });
    }
});

// Manual consolidation trigger (optional — for a cron job or manual call)
app.post('/api/consolidate', async (req, res) => {
    try {
        const result = await callBridge({ action: "consolidate" });
        res.json(result);
    } catch (error) {
        res.status(500).json({ status: "error", message: error.message });
    }
});

// Brain health/status snapshot
app.get('/api/report', async (req, res) => {
    try {
        const result = await callBridge({ action: "report" });
        res.json(result);
    } catch (error) {
        res.status(500).json({ status: "error", message: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`\n==============================================`);
    console.log(` 🤖 PIKA v15 AUTONOMOUS SERVER IS ONLINE`);
    console.log(` 📡 Awaiting commands on http://localhost:${PORT}`);
    console.log(`==============================================\n`);
});
