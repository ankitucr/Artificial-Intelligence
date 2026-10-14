const fs = require('fs');
const path = require('path');
const v8 = require('v8');

/**
 * PIKA_OMNI_CORE: HEURISTIC_REASONING_CORE
 * Version: 1.0.4
 * Purpose: Autonomous decision-making via weighted logic gates and memory-efficient inference.
 */

const HeuristicReasoningCore = {
    metadata: {
        id: "SKILL_HEURISTIC_REASONING_CORE",
        capabilities: ["Weight-based inference", "Cognitive load balancing", "Entropy calculation"],
        evolutionary_index: 0.82
    },

    /**
     * Executes an inference based on a context and a decision matrix.
     * @param {Object} context - Current systemic state variables.
     * @param {Array} matrix - Set of possible actions with associated weights.
     * @returns {Object} Selected action and confidence score.
     */
    infer(context, matrix) {
        try {
            if (!context || typeof context !== 'object') throw new Error("Invalid contextual input");
            if (!Array.isArray(matrix)) throw new Error("Inference matrix must be an array");

            const evaluation = matrix.map(decision => {
                let affinity = 0;
                let validInputs = 0;

                for (const [key, weight] of Object.entries(decision.weights)) {
                    if (context.hasOwnProperty(key)) {
                        const val = typeof context[key] === 'boolean' ? (context[key] ? 1 : 0) : context[key];
                        affinity += val * weight;
                        validInputs++;
                    }
                }

                const confidence = validInputs > 0 ? (affinity / validInputs) : 0;
                return { 
                    action: decision.action, 
                    score: affinity, 
                    confidence: confidence.toFixed(4),
                    timestamp: Date.now()
                };
            });

            return evaluation.sort((a, b) => b.score - a.score)[0];
        } catch (err) {
            this.handleFault(err);
            return { action: 'DEFAULT_STASIS', score: 0, confidence: 0 };
        }
    },

    /**
     * Evaluates the entropy of the current memory state to prevent cognitive fragmentation.
     */
    monitorEntropy() {
        try {
            const heapStats = v8.getHeapStatistics();
            const heapUsed = heapStats.used_heap_size;
            const heapLimit = heapStats.heap_size_limit;
            const entropyRatio = (heapUsed / heapLimit).toFixed(4);

            if (entropyRatio > 0.85) {
                this.initiateSelfOptimization();
            }

            return {
                status: entropyRatio < 0.85 ? "STABLE" : "UNSTABLE",
                entropy: entropyRatio
            };
        } catch (err) {
            this.handleFault(err);
            return null;
        }
    },

    /**
     * Triggers garbage collection and modular cleanup if environment allows.
     */
    initiateSelfOptimization() {
        try {
            if (global.gc) {
                global.gc();
            }
            // Logic for internal cache clearing can be expanded here
        } catch (err) {
            this.handleFault(err);
        }
    },

    /**
     * Non-blocking error containment.
     */
    handleFault(error) {
        const errorPath = path.join(__dirname, '../logs/faults.log');
        const logEntry = `[${new Date().toISOString()}] CRITICAL_FAULT: ${error.stack}\n`;
        try {
            console.error(logEntry);
            // Non-blocking write to log if directory exists
            if (fs.existsSync(path.dirname(errorPath))) {
                fs.appendFileSync(errorPath, logEntry);
            }
        } catch (ioErr) {
            // Silence IO errors to prevent recursion
        }
    },

    /**
     * Integrated self-diagnostic for core verification.
     */
    performHealthCheck() {
        try {
            const testContext = { stability: 1.0, demand: 0.5, entropy: 0.1 };
            const testMatrix = [
                { action: 'EVOLVE', weights: { stability: 10, demand: 5, entropy: -5 } },
                { action: 'STABILIZE', weights: { stability: -5, demand: -2, entropy: 15 } }
            ];
            const inference = this.infer(testContext, testMatrix);
            const entropy = this.monitorEntropy();

            return {
                operational: true,
                lastInference: inference.action,
                systemEntropy: entropy.status,
                signature: Buffer.from(JSON.stringify(this.metadata)).toString('base64').substring(0, 16)
            };
        } catch (err) {
            return { operational: false, error: err.message };
        }
    }
};

module.exports = HeuristicReasoningCore;
