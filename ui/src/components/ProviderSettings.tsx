"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Save, Lock, Check } from 'lucide-react';

const PROVIDERS = [
    { id: 'openai', name: 'OpenAI (GPT-4o)', type: 'openai' },
    { id: 'deepseek', name: 'DeepSeek', type: 'openai-compatible' },
    { id: 'claude', name: 'Anthropic Claude', type: 'anthropic' },
];

export default function ProviderSettings({ onClose }: { onClose: () => void }) {
    const [configs, setConfigs] = useState<any>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetch('http://localhost:8010/config')
            .then(res => res.json())
            .then(data => {
                setConfigs(data);
                setLoading(false);
            });
    }, []);

    const handleSave = async (providerId: string, apiKey: string) => {
        setSaving(true);
        await fetch(`http://localhost:8010/config/${providerId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ apiKey })
        });

        // 重新获取状态
        const res = await fetch('http://localhost:8010/config');
        const data = await res.json();
        setConfigs(data);
        setSaving(false);
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        >
            <div className="w-full max-w-lg glass-panel rounded-3xl overflow-hidden shadow-[0_0_50px_rgba(112,0,255,0.2)]">
                <div className="p-6 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-cyber-purple/10 to-transparent">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-cyber-purple/20 rounded-lg">
                            <Lock className="w-5 h-5 text-cyber-purple" />
                        </div>
                        <h2 className="text-xl font-bold tracking-tight">ENGINE CONFIGURATION</h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {PROVIDERS.map((provider) => (
                        <div key={provider.id} className="space-y-3">
                            <div className="flex items-center justify-between px-1">
                                <label className="text-sm font-semibold text-gray-300">{provider.name}</label>
                                {configs[provider.id]?.hasKey && (
                                    <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold uppercase tracking-widest">
                                        <Check className="w-3 h-3" /> Configured
                                    </span>
                                )}
                            </div>
                            <div className="flex gap-2">
                                <input
                                    type="password"
                                    placeholder="sk-••••••••••••••••••••••••"
                                    className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-cyber-purple/50 transition-colors font-mono"
                                    id={`key-${provider.id}`}
                                />
                                <button
                                    onClick={() => {
                                        const input = document.getElementById(`key-${provider.id}`) as HTMLInputElement;
                                        handleSave(provider.id, input.value);
                                        input.value = '';
                                    }}
                                    disabled={saving}
                                    className="px-4 bg-white/5 border border-white/10 hover:bg-cyber-purple/20 hover:border-cyber-purple/40 rounded-xl transition-all disabled:opacity-50"
                                >
                                    <Save className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="p-6 bg-white/5 border-t border-white/10 text-center">
                    <p className="text-[10px] text-gray-500 font-mono italic">
                        All API keys are encrypted and stored locally on your machine.
                    </p>
                </div>
            </div>
        </motion.div>
    );
}
