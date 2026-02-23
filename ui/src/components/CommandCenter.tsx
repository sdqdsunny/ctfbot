"use client";

import React, { useState } from 'react';
import {
    Terminal,
    Cpu,
    Shield,
    Search,
    MessageSquare,
    Zap,
    Settings,
    Globe,
    Lock,
    Flag
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ProviderSettings from './ProviderSettings';
import ProcessGraph from './ProcessGraph';
import PayloadInspector from './PayloadInspector';
import OrchestratorChat from './OrchestratorChat';

const MODELS = [
    { id: 'deepseek', name: 'DeepSeek R1', color: '#3B82F6' },
    { id: 'openai', name: 'GPT-4o', color: '#10B981' },
    { id: 'claude', name: 'Claude 3.5', color: '#F59E0B' },
];

export default function CommandCenter() {
    const [activeModel, setActiveModel] = useState(MODELS[0]);
    const [url, setUrl] = useState('');
    const [showSettings, setShowSettings] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

    return (
        <div className="flex flex-col h-screen w-full bg-background text-foreground overflow-hidden">
            {/* Top Navigation / Pilot Deck */}
            <header className="h-16 glass-panel border-b border-white/10 flex items-center justify-between px-6 z-50">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-cyber-blue/20 rounded-lg flex items-center justify-center border border-cyber-blue/40 shadow-[0_0_10px_rgba(0,242,255,0.3)]">
                        <Cpu className="text-cyber-blue w-6 h-6" />
                    </div>
                    <h1 className="text-xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-cyber-blue to-cyber-purple">
                        CTF-ASAS COMMAND CENTER
                    </h1>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
                        {MODELS.map((model) => (
                            <button
                                key={model.id}
                                onClick={() => setActiveModel(model)}
                                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-300 ${activeModel.id === model.id
                                    ? 'bg-white/10 text-white shadow-lg'
                                    : 'text-gray-400 hover:text-white'
                                    }`}
                            >
                                {model.name}
                            </button>
                        ))}
                    </div>
                    <button
                        onClick={() => setShowSettings(true)}
                        className="p-2 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors"
                    >
                        <Settings className="w-5 h-5 text-gray-400" />
                    </button>
                </div>
            </header>

            {/* Main Layout */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left Sidebar - Armory */}
                <aside className="w-64 glass-panel border-r border-white/10 p-4 flex flex-col gap-6">
                    <div className="space-y-4">
                        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2">Mission Control</h2>
                        <div className="space-y-1">
                            {['Binary Exploit', 'Web Security', 'Cryptography', 'Reverse'].map((cat) => (
                                <button key={cat} className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all group">
                                    <Shield className="w-4 h-4 group-hover:text-cyber-blue" />
                                    {cat}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="mt-auto p-4 rounded-xl bg-cyber-blue/5 border border-cyber-blue/10">
                        <div className="flex items-center gap-2 mb-2">
                            <Zap className="w-4 h-4 text-cyber-blue" />
                            <span className="text-xs font-bold text-cyber-blue">Core Status</span>
                        </div>
                        <div className="text-[10px] text-gray-400 font-mono">
                            Uptime: 04:22:15<br />
                            Agents: 3 Active<br />
                            Threads: 128
                        </div>
                    </div>
                </aside>

                {/* Center - The Core Visualization */}
                <main className="flex-1 relative flex flex-col">
                    {/* URL Input Bar */}
                    <div className="p-4 glass-panel border-b border-white/10 mt-4 mx-4 rounded-2xl flex gap-3">
                        <div className="flex-1 relative">
                            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                                <Globe className="h-4 w-4 text-gray-500" />
                            </div>
                            <input
                                type="text"
                                placeholder="Target URL / IP Address"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                className="w-full bg-black/40 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-cyber-blue/50 transition-colors font-mono"
                            />
                        </div>
                        <button
                            onClick={() => setIsAnalyzing(!isAnalyzing)}
                            className="px-6 py-2 bg-gradient-to-r from-cyber-blue to-cyber-purple text-white rounded-xl text-sm font-bold shadow-[0_0_15px_rgba(0,242,255,0.2)] hover:shadow-cyber-blue/40 transition-all flex items-center gap-2"
                        >
                            <Search className="w-4 h-4" />
                            {isAnalyzing ? 'ABORT' : 'ANALYZE'}
                        </button>
                    </div>

                    {/* Visualization Area */}
                    <div className="flex-1 flex items-center justify-center overflow-hidden">
                        {isAnalyzing ? (
                            <div className="w-full h-full relative">
                                <ProcessGraph onNodeSelect={setSelectedNodeId} />
                            </div>
                        ) : (
                            <div className="text-center opacity-20 group cursor-default">
                                <Flag className="w-32 h-32 mx-auto mb-4 text-cyber-blue transition-transform group-hover:scale-110" />
                                <p className="text-xl font-mono tracking-[0.5em] text-cyber-blue">WAITING FOR TARGET</p>
                            </div>
                        )}
                    </div>
                </main>

                <OrchestratorChat />
            </div>

            <AnimatePresence>
                {showSettings && (
                    <ProviderSettings onClose={() => setShowSettings(false)} />
                )}
                {selectedNodeId && (
                    <PayloadInspector nodeId={selectedNodeId} onClose={() => setSelectedNodeId(null)} />
                )}
            </AnimatePresence>
        </div>
    );
}
