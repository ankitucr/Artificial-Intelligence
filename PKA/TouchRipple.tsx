// =====================================================================
// 🌊 PKA TOUCHRIPPLE.TSX : THE NEURAL INTERFACE PULSE [FINAL LEVEL]
// Interactive UI Feedback | Framer Motion Optimized
// =====================================================================

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const TouchRipple = () => {
    const [ripples, setRipples] = useState<{ id: number; x: number; y: number }[]>([]);

    const addRipple = useCallback((e: React.MouseEvent | React.TouchEvent) => {
        const x = 'touches' in e ? e.touches[0].clientX : (e as React.MouseEvent).clientX;
        const y = 'touches' in e ? e.touches[0].clientY : (e as React.MouseEvent).clientY;

        const newRipple = { id: Date.now(), x, y };
        setRipples(prev => [...prev, newRipple]);

        setTimeout(() => {
            setRipples(prev => prev.filter(r => r.id !== newRipple.id));
        }, 1500); // 🟢 FINAL LEVEL: Slightly longer duration for "Deep Pulse"
    }, []);

    return (
        <div 
            className="absolute inset-0 z-0 overflow-hidden pointer-events-none" 
            onMouseDown={addRipple}
        >
            <AnimatePresence>
                {ripples.map(ripple => (
                    <motion.div
                        key={ripple.id}
                        initial={{ scale: 0, opacity: 0.8 }}
                        animate={{ 
                            scale: 6, // 🟢 FINAL LEVEL: Bigger expansion
                            opacity: 0,
                            boxShadow: "0 0 50px rgba(57, 255, 20, 0.5)" // Neural Glow
                        }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                        style={{
                            position: "absolute",
                            left: ripple.x,
                            top: ripple.y,
                            width: 100,
                            height: 100,
                            marginLeft: -50,
                            marginTop: -50,
                            borderRadius: "50%",
                            background: "radial-gradient(circle, rgba(57, 255, 20, 0.4) 0%, transparent 70%)", // 🟢 PKA Brand Color
                            pointerEvents: "none"
                        }}
                    />
                ))}
            </AnimatePresence>
        </div>
    );
};
