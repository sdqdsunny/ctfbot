import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle2, XCircle, Clock, Zap } from 'lucide-react';

export type AgentNodeData = {
    label: string;
    status: 'pending' | 'running' | 'success' | 'error';
    agentType?: string;
    details?: string;
};

const statusColors = {
    pending: 'border-gray-500/50 text-gray-400 bg-gray-900/40',
    running: 'border-cyber-blue/50 text-cyber-blue bg-cyber-blue/10 shadow-[0_0_15px_rgba(0,242,255,0.2)]',
    success: 'border-emerald-500/50 text-emerald-400 bg-emerald-500/10 shadow-[0_0_15px_rgba(16,185,129,0.2)]',
    error: 'border-rose-500/50 text-rose-400 bg-rose-500/10 shadow-[0_0_15px_rgba(244,63,94,0.2)]'
};

const StatusIcon = ({ status }: { status: AgentNodeData['status'] }) => {
    switch (status) {
        case 'running': return <Loader2 className="w-3 h-3 animate-spin" />;
        case 'success': return <CheckCircle2 className="w-3 h-3" />;
        case 'error': return <XCircle className="w-3 h-3" />;
        default: return <Clock className="w-3 h-3" />;
    }
};

export default function AgentNode({ data, selected }: NodeProps<AgentNodeData>) {
    const isRunning = data.status === 'running';

    return (
        <motion.div
            whileHover={{ scale: 1.05 }}
            className={`
                relative min-w-[160px] p-3 rounded-xl border backdrop-blur-md transition-all duration-300
                ${statusColors[data.status]}
                ${selected ? 'ring-2 ring-cyber-purple ring-offset-2 ring-offset-[#0b0e14]' : ''}
            `}
        >
            {/* Animated border pulse for running state */}
            {isRunning && (
                <div className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none">
                    <div className="absolute inset-0 border-2 border-cyber-blue opacity-50 animate-ping" />
                </div>
            )}

            <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-cyber-purple !border-[#0b0e14]" />

            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest opacity-80">
                        {data.agentType === 'orchestrator' ? <Zap className="w-3 h-3 text-amber-400" /> : null}
                        {data.agentType || 'Agent'}
                    </div>
                    <StatusIcon status={data.status} />
                </div>

                <div className="font-mono text-xs font-semibold">
                    {data.label}
                </div>

                {data.details && (
                    <div className="text-[9px] opacity-60 truncate max-w-[140px]">
                        {data.details}
                    </div>
                )}
            </div>

            <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-cyber-purple !border-[#0b0e14]" />
        </motion.div>
    );
}
