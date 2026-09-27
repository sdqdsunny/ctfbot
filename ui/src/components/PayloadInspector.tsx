"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Code, Terminal, FileText, ExternalLink, BookOpen } from 'lucide-react';
import { analyzePayload } from '../utils/toolDictionary';
import { AgentEvent } from '../hooks/useAgentEvents';
import { useGraphData } from '../hooks/useGraphData';

interface PayloadInspectorProps {
    nodeId: string | null;
    onClose: () => void;
    data?: {
        title: string;
        payload: string;
        logs: string;
        conclusion: string;
    };
    events?: AgentEvent[];
    isEducationalMode?: boolean;
}

export default function PayloadInspector({ nodeId, onClose, data, events = [], isEducationalMode = false }: PayloadInspectorProps) {
    const { stepData } = useGraphData(events);

    if (!nodeId) return null;

    // Use live step data if available, otherwise fallback to prop data (or mock)
    const liveData = stepData[nodeId] || data;
    const payloadText = liveData?.payload || "No payload generated yet.";
    const stepLogs = liveData?.logs || "Waiting for execution logs...";
    const stepConclusion = liveData?.conclusion || "Waiting for agent reasoning conclusion...";

    // Simple heuristic to guess the tool from the payload string
    let toolName = "kali_exec";
    if (payloadText.includes('sqlmap')) toolName = 'kali_sqlmap';
    if (payloadText.includes('nmap')) toolName = 'kali_nmap';

    const analysis = analyzePayload(toolName, { command: payloadText });

    return (
        <AnimatePresence>
            <motion.div
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="fixed right-0 top-16 bottom-0 w-[500px] glass-panel border-l border-white/10 z-[60] flex flex-col shadow-[-20px_0_50px_rgba(0,0,0,0.5)]"
            >
                <div className="p-6 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-cyber-blue/10 to-transparent">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-cyber-blue/20 rounded-lg">
                            <Terminal className="w-5 h-5 text-cyber-blue" />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold tracking-widest text-cyber-blue uppercase">Step Inspector</h2>
                            <p className="text-[10px] text-gray-500 font-mono">ID: {nodeId}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    {/* Summary / Conclusion */}
                    <section className="space-y-3">
                        <div className="flex items-center gap-2 text-xs font-bold text-gray-400">
                            <FileText className="w-4 h-4" /> REASONING CONCLUSION
                        </div>
                        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-sm leading-relaxed text-gray-300 italic">
                            {stepConclusion}
                        </div>
                    </section>

                    {/* Payload Section */}
                    <section className="space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-xs font-bold text-gray-400">
                                <Code className="w-4 h-4" /> GENERATED PAYLOAD
                            </div>
                            <button className="text-[10px] text-cyber-blue hover:underline flex items-center gap-1">
                                COPY <ExternalLink className="w-2 h-2" />
                            </button>
                        </div>
                        <div className="bg-black/60 rounded-xl p-4 border border-white/10 font-mono text-xs text-cyber-pink overflow-x-auto whitespace-pre">
                            <code>{payloadText}</code>
                        </div>
                    </section>

                    {/* Educational Anatomy Section */}
                    {isEducationalMode && analysis && (
                        <div className="mt-4 border-t border-white/10 pt-4">
                            <div className="flex items-center gap-2 mb-2 text-cyber-blue font-mono text-[11px] uppercase tracking-wider">
                                <BookOpen className="w-3 h-3" />
                                Tool Anatomy Room
                            </div>
                            <div className="bg-white/5 rounded-md p-3 border border-white/5">
                                <h4 className="text-white text-xs font-bold mb-1">{analysis.anatomy.name}</h4>
                                <p className="text-gray-400 text-[10px] mb-3 leading-relaxed">{analysis.anatomy.description}</p>

                                {analysis.detected.length > 0 && (
                                    <div className="space-y-2">
                                        <div className="text-[9px] uppercase tracking-wider text-gray-500 font-bold">Detected Flags</div>
                                        {analysis.detected.map((item, idx) => (
                                            <div key={idx} className="flex flex-col gap-0.5">
                                                <code className="text-[10px] text-cyber-pink font-mono bg-cyber-pink/10 px-1 py-0.5 rounded w-fit">
                                                    {item.flag}
                                                </code>
                                                <span className="text-gray-400 text-[10px]">{item.meaning}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Raw Logs Section */}
                    <section className="space-y-3 pb-8">
                        <div className="flex items-center gap-2 text-xs font-bold text-gray-400">
                            <Terminal className="w-4 h-4" /> RAW EXECUTION LOGS
                        </div>
                        <div className="bg-black/80 rounded-xl p-4 border border-white/5 font-mono text-[10px] text-emerald-500 h-64 overflow-y-auto whitespace-pre-wrap">
                            {stepLogs}
                        </div>
                    </section>
                </div>

                <div className="p-4 bg-white/5 border-t border-white/10 flex gap-2">
                    <button className="flex-1 py-2 bg-cyber-blue/10 border border-cyber-blue/30 text-cyber-blue rounded-xl text-xs font-bold hover:bg-cyber-blue/20 transition-all uppercase tracking-widest">
                        Approve & Execute
                    </button>
                    <button className="px-4 py-2 bg-white/5 border border-white/10 text-gray-400 rounded-xl text-xs font-bold hover:bg-white/10 transition-all uppercase tracking-widest">
                        Modify
                    </button>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
