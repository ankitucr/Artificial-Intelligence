// =====================================================================
// 🛠️ PKA SYSTEM TOOLS : OS-LEVEL ACCESS & AGENTIC CONTROL (FINAL GOD-MODE)
// 100% API-FREE | Local Security | Python Runner | Auto-Debug (DuckDuckGo)
// =====================================================================

const { exec } = require("child_process");
const os = require("os");
const fs = require("fs");
const path = require("path");
const { search } = require("duck-duck-scrape"); // 🕸️ NEW: Web-Powered Auto-Debugging

class PKASystemTools {
    constructor() {
        console.log("\x1b[36m%s\x1b[0m", "💻 [SYSTEM_TOOLS] OS-Level Access Granted. Auto-Debug Engine Ready.");
    }

    // =========================================================
    // 🕸️ 1. AUTONOMOUS WEB-DEBUGGER (DuckDuckGo Powered)
    // =========================================================
    async resolveErrorFromWeb(errorMessage) {
        console.log(`\n🕵️‍♂️ [AUTO-DEBUG] Scanning Deep Web for error fix...`);
        try {
            // Clean error message for better search results
            const cleanError = errorMessage.replace(/[^a-zA-Z0-9 :\-\.]/g, " ").substring(0, 80);
            const query = `How to fix error: ${cleanError} stackoverflow github`;
            
            const searchResults = await search(query, { safeSearch: "moderate" });
            
            if (searchResults.results && searchResults.results.length > 0) {
                let fixInsight = searchResults.results[0].description;
                console.log(`✅ [DEBUG SUCCESS] Found Potential Fix: ${fixInsight.substring(0, 100)}...`);
                return fixInsight;
            }
            return "No obvious fix found on the open web.";
        } catch (err) {
            console.log(`⚠️ [DEBUG OFFLINE] Web Scraper blocked. Error: ${err.message}`);
            return "Web Scraper offline.";
        }
    }

    // =========================================================
    // ⚡ 2. SHELL COMMAND EXECUTOR (With Auto-Debug)
    // =========================================================
    async executeShellCommand(command, autoDebug = true) {
        return new Promise((resolve) => {
            console.log(`\n⚙️ [SYS-EXEC] Executing: ${command}`);

            // 🟢 LOCAL AI INTENT AUDIT (Prevents Suicide)
            const dangerousPatterns = [
                "rm -rf /", "mkfs", ":(){:|:&};:", "> /dev/sda", 
                "chmod -R 777 /", "wget http", "curl http"
            ];
            
            const isHardBlocked = dangerousPatterns.some(kw => command.toLowerCase().includes(kw));

            if (isHardBlocked) {
                console.log("\x1b[31m%s\x1b[0m", "🛑 [SYS-BLOCK] Blocked dangerous system-wipe command!");
                return resolve({ success: false, output: "Safety Restriction: Command Blocked." });
            }

            exec(command, async (error, stdout, stderr) => {
                if (error) {
                    console.error(`\x1b[31m%s\x1b[0m`, `❌ [SYS-ERROR] Command Failed.`);
                    
                    let suggestedFix = "None";
                    // 🕸️ Trigger DuckDuckGo if command fails!
                    if (autoDebug) {
                        suggestedFix = await this.resolveErrorFromWeb(stderr || error.message);
                    }

                    resolve({ success: false, output: stderr, errorMsg: error.message, fix: suggestedFix });
                } else {
                    console.log(`\x1b[32m%s\x1b[0m`, `✅ [SYS-SUCCESS] Command Executed.`);
                    resolve({ success: true, output: stdout });
                }
            });
        });
    }

    // =========================================================
    // 🐍 3. AUTONOMOUS PYTHON RUNNER (Safe Temp Execution)
    // =========================================================
    async runPythonScript(pythonCode) {
        const tempFilePath = path.join(os.tmpdir(), `pka_script_${Date.now()}.py`);

        try {
            console.log(`🐍 [PYTHON] Spinning up temporary ML environment...`);
            fs.writeFileSync(tempFilePath, pythonCode);

            const result = await this.executeShellCommand(`python3 ${tempFilePath} || python ${tempFilePath}`, true);

            return result;
        } catch (error) {
            console.error(`❌ [PYTHON-ERROR] Script failed:`, error.message);
            return { success: false, error: error.message };
        } finally {
            if (fs.existsSync(tempFilePath)) fs.unlinkSync(tempFilePath);
        }
    }

    // =========================================================
    // 📊 4. SYSTEM HEALTH & RESOURCE GUARD (Proactive)
    // =========================================================
    getSystemHealth() {
        const freeRAM = (os.freemem() / (1024 ** 3)).toFixed(2);
        const totalRAM = (os.totalmem() / (1024 ** 3)).toFixed(2);
        const usedRAM = (totalRAM - freeRAM).toFixed(2);

        console.log(`📊 [SYS-HEALTH] RAM: ${freeRAM}GB Free / ${totalRAM}GB Total`);

        // 🟢 AUTO-HEAL: Trigger Cleaner if RAM is running low (< 10%)
        if (parseFloat(freeRAM) < (parseFloat(totalRAM) * 0.1)) {
            console.log("\x1b[33m%s\x1b[0m", "⚠️ [LOW-RESOURCE] Triggering Neural Cleaner to free up RAM...");
            
            const cleanerPath = path.resolve(__dirname, "..", "cleaner.js"); 
            if (fs.existsSync(cleanerPath)) {
                this.executeShellCommand(`node "${cleanerPath}"`, false); // Auto-debug false here to avoid loops
            } else {
                console.log("⚠️ cleaner.js not found at expected path.");
            }
        }

        return {
            os: os.platform(),
            cpu: os.cpus().length,
            ram: { total: `${totalRAM} GB`, used: `${usedRAM} GB`, free: `${freeRAM} GB` },
            uptime: `${(os.uptime() / 3600).toFixed(2)} Hours`
        };
    }

    // =========================================================
    // 📦 5. AUTO-INSTALLER (Self-Healing NPM)
    // =========================================================
    async installPackage(packageName, manager = "npm") {
        console.log(`📦 [AUTO-INSTALL] Installing required library: ${packageName}...`);
        
        const safePackageName = packageName.replace(/[^a-zA-Z0-9\-_@\.]/g, ''); 
        const command = manager === "npm" ? `npm install ${safePackageName}` : `pip install ${safePackageName}`;

        const result = await this.executeShellCommand(command, true);
        if (result.success) {
            console.log(`✅ [INSTALLED] ${safePackageName} is now part of PKA DNA.`);
        } else {
            console.log(`⚠️ [INSTALL FAIL] PKA suggests: ${result.fix}`);
        }
        return result;
    }
}

module.exports = new PKASystemTools();
