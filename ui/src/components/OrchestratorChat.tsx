"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Zap, Terminal, User, Bot, Loader2 } from 'lucide-react';

import { useAgentEvents, AgentEvent } from '../hooks/useAgentEvents';

interface Message {
    id: string;
    type: 'system' | 'agent' | 'user';
    content: string;
    timestamp: string;
}

export default function OrchestratorChat() {
    const events = useAgentEvents();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            type: 'system',
            content: 'Command Center Online. Orchestrator ready for instructions.',
            timestamp: new Date().toLocaleTimeString()
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    useEffect(() => {
        if (events.length === 0) return;
        const lastEvent = events[events.length - 1];

        // Define simple typing for the payload to satisfy TS
        const data = lastEvent.data as Record<string, unknown>;

        if (lastEvent.type === 'orchestrator_message') {
            const content = data.content as string | undefined;
            const tool_calls = data.tool_calls as Array<{ name: string, args: Record<string, unknown> }>;

            const text = content ? String(content) : `Executing tools: ${tool_calls.map(t => t.name).join(', ')}`;

            // eslint-disable-next-line react-hooks/set-state-in-effect
            setMessages(prev => [...prev, {
                id: lastEvent.timestamp.toString(),
                type: 'agent',
                content: text,
                timestamp: new Date(lastEvent.timestamp).toLocaleTimeString()
            }]);
            setIsTyping(false);
        } else if (lastEvent.type === 'tool_result') {
            const tool_name = data.tool_name as string;
            const content = String(data.content);
            const is_error = Boolean(data.is_error);

            // eslint-disable-next-line react-hooks/set-state-in-effect
            setMessages(prev => [...prev, {
                id: lastEvent.timestamp.toString(),
                type: 'system',
                content: `[${tool_name}] ${is_error ? 'FAILED' : 'SUCCESS'}: ${content.substring(0, 100)}...`,
                timestamp: new Date(lastEvent.timestamp).toLocaleTimeString()
            }]);
        }
    }, [events]);

    const handleSendMessage = () => {
        if (!inputValue.trim()) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            type: 'user',
            content: inputValue,
            timestamp: new Date().toLocaleTimeString()
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        // Note: Future integration can send this back via WebSocket or REST
        setTimeout(() => {
            setIsTyping(false);
        }, 5000);
    };

    return (
        <aside className="w-80 glass-panel border-l border-white/10 flex flex-col h-full overflow-hidden">
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-gradient-to-r from-cyber-purple/10 to-transparent">
                <div className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-cyber-purple shadow-[0_0_10px_rgba(112,0,255,0.4)]" />
                    <span className="font-bold text-sm tracking-tight text-gray-200">ORCHESTRATOR UPLINK</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] text-emerald-500 font-bold tracking-widest uppercase">Live</span>
                </div>
            </div>

            <div
                ref={scrollRef}
                className="flex-1 p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar"
            >
                <AnimatePresence initial={false}>
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            className={`flex flex-col gap-1.5 ${msg.type === 'user' ? 'items-end' : 'items-start'}`}
                        >
                            <div className={`flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest ${msg.type === 'user' ? 'text-cyber-blue flex-row-reverse' : msg.type === 'agent' ? 'text-cyber-purple' : 'text-gray-500'
                                }`}>
                                {msg.type === 'user' ? <User className="w-3 h-3" /> : msg.type === 'agent' ? <Bot className="w-3 h-3" /> : <Terminal className="w-3 h-3" />}
                                {msg.type}
                            </div>
                            <div className={`p-3 rounded-2xl text-xs font-mono leading-relaxed max-w-[90%] border ${msg.type === 'user'
                                ? 'bg-cyber-blue/10 border-cyber-blue/30 text-cyber-blue rounded-tr-none'
                                : msg.type === 'agent'
                                    ? 'bg-cyber-purple/10 border-cyber-purple/30 text-cyber-purple rounded-tl-none shadow-[0_0_15px_rgba(112,0,255,0.05)]'
                                    : 'bg-white/5 border-white/10 text-gray-400 font-italic text-[11px]'
                                }`}>
                                {msg.content}
                                <div className="mt-1 text-[9px] opacity-40 text-right">{msg.timestamp}</div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {isTyping && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center gap-2 text-cyber-purple/60 italic text-[10px] font-mono"
                    >
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Orchestrator is processing...
                    </motion.div>
                )}
            </div>

            <div className="p-4 border-t border-white/10 bg-black/20">
                <div className="relative group">
                    <input
                        type="text"
                        placeholder="Direct instruction..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-4 pr-10 text-xs focus:outline-none focus:border-cyber-purple/50 focus:bg-white/10 transition-all font-mono placeholder:text-gray-600"
                    />
                    <button
                        onClick={handleSendMessage}
                        className="absolute right-2 top-2 p-1 text-cyber-purple hover:text-white transition-colors group-focus-within:animate-pulse"
                    >
                        <Zap className="w-4 h-4 fill-cyber-purple/20" />
                    </button>
                </div>
            </div>

            <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(112, 0, 255, 0.2);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(112, 0, 255, 0.4);
        }
      `}</style>
        </aside>
    );
}
