import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, ChevronDown } from 'lucide-react';

interface ThoughtPanelProps {
    thought: string;
}

export default function ThoughtPanel({ thought }: ThoughtPanelProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!thought) return null;

    return (
        <div className="mb-2 w-full max-w-[90%]">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-1.5 text-[10px] text-cyber-purple/70 hover:text-cyber-purple transition-colors bg-cyber-purple/5 px-2 py-1 rounded-md border border-cyber-purple/10 w-full"
            >
                <Brain className="w-3 h-3" />
                <span className="font-mono uppercase tracking-wider font-semibold">Agent Reasoning</span>
                <motion.div
                    animate={{ rotate: isExpanded ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="ml-auto"
                >
                    <ChevronDown className="w-3 h-3" />
                </motion.div>
            </button>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="p-2.5 mt-1 rounded-md text-[10px] font-mono leading-relaxed bg-black/40 border border-cyber-purple/20 text-gray-400 italic whitespace-pre-wrap">
                            {thought}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
