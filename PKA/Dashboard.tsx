import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, TrendingUp, Activity, ShieldAlert } from 'lucide-react';

const PKADashboard = () => {
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        const interval = setInterval(() => {
            fetch('http://localhost:3001/api/pka-data')
                .then(res => res.json())
                .then(json => setData(json));
        }, 2000); // Har 2 sec me Refresh
        return () => clearInterval(interval);
    }, []);

    if (!data) return <div className="bg-black text-green-500 h-screen flex items-center justify-center font-mono">📡 INITIATING NEURAL LINK...</div>;

    return (
        <div className="bg-black text-green-400 min-h-screen p-6 font-mono selection:bg-green-900">
            {/* Header: Global Sync Status */}
            <div className="flex justify-between items-center border-b border-green-900 pb-4 mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tighter uppercase">P.K.A. Neural Core</h1>
                    <p className="text-xs text-green-600">Evolution State: <span className="animate-pulse">{data.state.status}</span></p>
                </div>
                <div className="text-right">
                    <p className="text-xs">Intelligence Baseline: {data.version}</p>
                    <p className="text-xl font-bold">{data.state.intelligence.toFixed(2)} IQ</p>
                </div>
            </div>

            {/* Grid Layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                
                {/* Sector 1: Portfolio (Broker API) */}
                <motion.div whileHover={{ scale: 1.02 }} className="border border-green-800 p-4 bg-green-950/10 rounded-lg">
                    <div className="flex items-center gap-2 mb-4 text-green-300">
                        <TrendingUp size={20} /> <span className="font-bold">FINANCIAL ASSETS</span>
                    </div>
                    <p className="text-3xl font-bold text-white">${data.portfolio.balance.toLocaleString()}</p>
                    <div className="mt-4 text-xs space-y-1">
                        <p>PnL: <span className={data.portfolio.totalPnL >= 0 ? "text-green-400" : "text-red-400"}>${data.portfolio.totalPnL}</span></p>
                        <p>Win Rate: {data.portfolio.winRate}%</p>
                    </div>
                </motion.div>

                {/* Sector 2: Neural Mastery */}
                <motion.div whileHover={{ scale: 1.02 }} className="border border-green-800 p-4 bg-green-950/10 rounded-lg">
                    <div className="flex items-center gap-2 mb-4 text-green-300">
                        <Brain size={20} /> <span className="font-bold">NEURAL MASTERY</span>
                    </div>
                    <div className="space-y-3 text-xs">
                        {Object.entries(data.state.mastery).map(([key, val]: any) => (
                            <div key={key}>
                                <div className="flex justify-between mb-1">
                                    <span className="capitalize">{key.replace('_', ' ')}</span>
                                    <span>{(val * 100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-green-900/30 h-1.5 rounded-full overflow-hidden">
                                    <div className="bg-green-500 h-full" style={{ width: `${val * 100}%` }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Sector 3: System Health */}
                <motion.div whileHover={{ scale: 1.02 }} className="border border-green-800 p-4 bg-green-950/10 rounded-lg">
                    <div className="flex items-center gap-2 mb-4 text-green-300">
                        <Activity size={20} /> <span className="font-bold">CORE HEALTH</span>
                    </div>
                    <div className="text-sm space-y-4">
                        <div>
                            <p className="text-xs text-green-700">RAM Status</p>
                            <p className="font-bold">{data.health.ram}</p>
                        </div>
                        <div>
                            <p className="text-xs text-green-700">System Uptime</p>
                            <p className="font-bold">{data.health.uptime}</p>
                        </div>
                    </div>
                </motion.div>

                {/* Sector 4: Alert Logs (Memory) */}
                <motion.div whileHover={{ scale: 1.02 }} className="border border-red-900/50 p-4 bg-red-950/5 rounded-lg">
                    <div className="flex items-center gap-2 mb-4 text-red-400">
                        <ShieldAlert size={20} /> <span className="font-bold">NEURAL LOGS</span>
                    </div>
                    <div className="text-[10px] space-y-2 opacity-70">
                        <p className="border-l border-red-500 pl-2">SYNC_COMPLETE: {new Date().toLocaleTimeString()}</p>
                        <p className="border-l border-red-500 pl-2">TRD_ENGINE: ACTIVE</p>
                        <p className="border-l border-red-500 pl-2">EVOLUTION: HYPER_CONSCIOUS</p>
                    </div>
                </motion.div>

            </div>

            {/* Background Grid Pattern */}
            <div className="fixed inset-0 opacity-[0.03] pointer-events-none z-[-1] overflow-hidden">
                <div className="grid grid-cols-12 h-full w-full">
                    {[...Array(144)].map((_, i) => (
                        <div key={i} className="border border-green-500 h-32 w-32"></div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default PKADashboard;
