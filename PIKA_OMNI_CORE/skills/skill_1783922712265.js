/**
 * @module MemoryOptimizer
 * @description Optimizes cognitive load by pruning redundant state transitions and maintaining heap integrity.
 */
const MemoryOptimizer = {
    id: "SKILL_MEM_OPT_001",
    version: "1.0.4",

    /**
     * Prunes a state buffer to ensure unique, high-priority cognitive frames.
     * @param {Array} stateBuffer - The array of state objects to optimize.
     * @returns {Object} Optimized state metadata.
     */
    optimize: function(stateBuffer) {
        try {
            if (!Array.isArray(stateBuffer)) {
                throw new Error("InvalidStateBuffer: Input must be an array.");
            }

            const initialCount = stateBuffer.length;
            if (initialCount === 0) return { status: "VOID", ratio: 0 };

            // Logic: Filter by ID uniqueness and priority weighting
            const seen = new Set();
            const optimizedBuffer = stateBuffer.filter(frame => {
                const duplicate = seen.has(frame.id);
                seen.add(frame.id);
                return !duplicate && (frame.priority > 0.2 || !frame.id);
            });

            return {
                status: "OPTIMIZED",
                initialLength: initialCount,
                finalLength: optimizedBuffer.length,
                compressionRatio: parseFloat((1 - (optimizedBuffer.length / initialCount)).toFixed(4)),
                timestamp: Date.now(),
                data: optimizedBuffer
            };
        } catch (error) {
            return {
                status: "CRITICAL_FAILURE",
                error: error.message,
                timestamp: Date.now()
            };
        }
    },

    /**
     * Performs a self-diagnostic on the optimization logic.
     * @returns {boolean}
     */
    healthCheck: function() {
        try {
            const testPayload = [
                { id: "A1", priority: 0.9 },
                { id: "A1", priority: 0.9 },
                { id: "B2", priority: 0.1 }
            ];
            const result = this.optimize(testPayload);
            // Should remove the duplicate and the low priority frame B2
            return result.status === "OPTIMIZED" && result.finalLength === 1;
        } catch {
            return false;
        }
    }
};

module.exports = MemoryOptimizer;