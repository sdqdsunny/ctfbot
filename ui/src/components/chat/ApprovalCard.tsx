import React, { useState } from 'react';
import { ShieldAlert, Check, X, Edit2, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

export interface ApprovalData {
    action_id: string;
    description: string;
    danger_level: 'low' | 'medium' | 'high';
    command?: string;
}

interface ApprovalCardProps {
    data: ApprovalData;
    onDecision: (approved: boolean, feedback?: string) => Promise<void>;
}

export default function ApprovalCard({ data, onDecision }: ApprovalCardProps) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [feedback, setFeedback] = useState('');
    const [showEdit, setShowEdit] = useState(false);

    const handleAction = async (approved: boolean) => {
        setIsSubmitting(true);
        try {
            await onDecision(approved, feedback);
        } finally {
            setIsSubmitting(false);
        }
    };

    const isHighRisk = data.danger_level === 'high';

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`
                flex flex-col gap-3 p-4 rounded-xl border
                ${isHighRisk ? 'bg-rose-500/10 border-rose-500/30' : 'bg-amber-500/10 border-amber-500/30'}
                mr-4 max-w-[90%]
            `}
        >
            <div className="flex items-center gap-2">
                <ShieldAlert className={`w-4 h-4 ${isHighRisk ? 'text-rose-500' : 'text-amber-500'}`} />
                <span className={`text-xs font-bold uppercase tracking-widest ${isHighRisk ? 'text-rose-500' : 'text-amber-500'}`}>
                    Action Requires Approval
                </span>
            </div>

            <p className="text-sm text-gray-300">
                {data.description}
            </p>

            {data.command && (
                <div className="p-3 bg-black/60 rounded-lg border border-white/5 font-mono text-xs text-gray-400 break-all">
                    <code>{data.command}</code>
                </div>
            )}

            {showEdit && (
                <input
                    type="text"
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Provide modification instructions..."
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-cyber-purple/50 transition-colors"
                />
            )}

            <div className="flex gap-2 mt-2">
                <button
                    onClick={() => handleAction(true)}
                    disabled={isSubmitting}
                    className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/30 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                    {isSubmitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                    Approve
                </button>
                <button
                    onClick={() => setShowEdit(!showEdit)}
                    disabled={isSubmitting}
                    className="flex-none px-3 flex items-center justify-center py-1.5 bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
                    title="Modify Instruction"
                >
                    <Edit2 className="w-3 h-3" />
                </button>
                <button
                    onClick={() => handleAction(false)}
                    disabled={isSubmitting}
                    className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-rose-500/20 border border-rose-500/30 text-rose-400 hover:bg-rose-500/30 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                >
                    {isSubmitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                    Reject
                </button>
            </div>
        </motion.div>
    );
}
