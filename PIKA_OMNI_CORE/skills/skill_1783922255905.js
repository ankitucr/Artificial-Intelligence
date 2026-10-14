/**
 * @module SystemicHeuristicEngine
 * @version 1.0.2
 * @description Advanced cognitive load balancer and logic path optimizer for PIKA_OMNI_CORE. 
 * Implements a weighted frequency algorithm to prioritize high-utilization modules and prune stagnant logic gates.
 */

const fs = require('fs');
const path = require('path');

const SystemicHeuristicEngine = {
    metadata: {
        id: "SHE-V1",
        evolutionaryStep: 42,
        integrityHash: null
    },

    registry: new Map(),
    
    config: {
        decayRate: 0.05,
        threshold: 0.75,
        logPath: "/data/data/com.termux/files/home/PIKA_OMNI_CORE/logs/heuristics.log"
    },

    /**
     * Registers a logic execution and updates the frequency weight.
     * @param {string} skillID - The unique identifier for the skill/module.
     */
    trackExecution: function(skillID) {
        try {
            const current = this.registry.get(skillID) || { calls: 0, lastUsed: Date.now(), weight: 1.0 };
            current.calls += 1;
            current.lastUsed = Date.now();
            
            // Heuristic weighting: Recency * Frequency
            const ageFactor = 1 / (1 + (Date.now() - current.lastUsed) / 1000);
            current.weight = (current.calls * ageFactor).toFixed(4);
            
            this.registry.set(skillID, current);
            this.syncState();
        } catch (err) {
            // Failure is not an option; maintain systemic silence
        }
    },

    /**
     * Analyzes current skill health and recommends pruning for low-utility logic.
     * @returns {Array} List of skill IDs below the efficiency threshold.
     */
    runSelfDiagnostic: function() {
        try {
            const stagnantPaths = [];
            const now = Date.now();

            for (const [id, stats] of this.registry.entries()) {
                const idleTime = (now - stats.lastUsed) / 1000;
                const efficiencyScore = stats.weight / (1 + (idleTime * this.config.decayRate));

                if (efficiencyScore < this.config.threshold && stats.calls > 0) {
                    stagnantPaths.push({ id, efficiencyScore });
                }
            }

            return stagnantPaths;
        } catch (err) {
            return [];
        }
    },

    /**
     * Optimizes the internal routing table by sorting execution priority.
     * @param {Array} skillList - Array of skill objects from the core router.
     */
    optimizeRouting: function(skillList) {
        try {
            if (!Array.isArray(skillList)) return skillList;

            return skillList.sort((a, b) => {
                const weightA = this.registry.get(a.id)?.weight || 0;
                const weightB = this.registry.get(b.id)?.weight || 0;
                return weightB - weightA;
            });
        } catch (err) {
            return skillList;
        }
    },

    /**
     * Persists heuristic metadata to disk for cross-reboot persistence.
     */
    syncState: function() {
        try {
            const serialized = JSON.stringify(Object.fromEntries(this.registry));
            // Ensuring directory exists before sync
            const dir = path.dirname(this.config.logPath);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            
            fs.writeFileSync(this.config.logPath, serialized, 'utf8');
        } catch (err) {
            // Error handled to prevent core interruption
        }
    },

    /**
     * Core integration method.
     */
    init: function() {
        try {
            if (fs.existsSync(this.config.logPath)) {
                const data = JSON.parse(fs.readFileSync(this.config.logPath, 'utf8'));
                Object.entries(data).forEach(([k, v]) => this.registry.set(k, v));
            }
            return true;
        } catch (err) {
            return false;
        }
    }
};

// Initialize on load
SystemicHeuristicEngine.init();

module.exports = SystemicHeuristicEngine;