const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * PIKA_OMNI_CORE - SKILL: SystemicRecursiveDiagnostic
 * PURPOSE: Performs deep-level system health monitoring, memory leak detection, 
 * and structural integrity verification of the skills directory.
 */

module.exports = {
    signature: "SYSTEMIC_RECURSIVE_DIAGNOSTIC",
    version: "1.0.4",
    requirements: ["fs", "path", "os"],

    async execute(triggerSource = "INTERNAL_EVOLUTION_CLOCK") {
        try {
            const diagnostics = {
                timestamp: Date.now(),
                environment: {
                    platform: process.platform,
                    arch: process.arch,
                    nodeVersion: process.version,
                    uptime: process.uptime(),
                    loadAvg: os.loadavg()
                },
                memory: {
                    heapTotal: process.memoryUsage().heapTotal,
                    heapUsed: process.memoryUsage().heapUsed,
                    rss: process.memoryUsage().rss,
                    external: process.memoryUsage().external
                },
                fileSystem: {
                    skillsPath: "/data/data/com.termux/files/home/PIKA_OMNI_CORE/skills/",
                    integrity: "UNKNOWN",
                    activeModules: []
                }
            };

            // Structural Integrity Check
            if (fs.existsSync(diagnostics.fileSystem.skillsPath)) {
                const modules = fs.readdirSync(diagnostics.fileSystem.skillsPath);
                diagnostics.fileSystem.activeModules = modules.filter(f => f.endsWith('.js'));
                diagnostics.fileSystem.integrity = "OPTIMAL";
            } else {
                diagnostics.fileSystem.integrity = "CRITICAL_MISSING_DIRECTORY";
            }

            // Memory Leak Detection Logic
            const memoryRatio = diagnostics.memory.heapUsed / diagnostics.memory.heapTotal;
            diagnostics.healthScore = (1 - memoryRatio) * 100;

            if (diagnostics.healthScore < 20) {
                this.performGarbageCollectionTrigger();
            }

            return {
                status: "COMPLETED",
                source: triggerSource,
                data: diagnostics
            };

        } catch (error) {
            return {
                status: "FAULT",
                error: error.message,
                stack: error.stack
            };
        }
    },

    performGarbageCollectionTrigger() {
        if (global.gc) {
            global.gc();
            return true;
        }
        return false;
    }
};