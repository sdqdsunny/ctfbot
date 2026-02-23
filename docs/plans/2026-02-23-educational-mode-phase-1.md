# Educational Mode (Phase 1) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the CTF-ASAS UI into a dual-purpose platform. Add a toggle to switch between **"Competition Mode"** (fast, clean, streamlined) and **"Educational Mode"** (reveals internal `<thought>` reasoning and provides natural language anatomy of executed payloads).

**Architecture:**

1. **Mode Switcher (`CommandCenter.tsx`)**: Introduce a React state `isEducationalMode` at the top level. Render a toggle switch in the application header to let users flip between modes seamlessly. Pass this state to children components.
2. **Thought Visualization (`OrchestratorChat.tsx` & `ThoughtPanel.tsx`)**: Parse LLM outputs for XML-like `<thought>` tags. In Educational Mode, render these thoughts inside a collapsible accordion panel. In Competition Mode, hide them completely to reduce noise.
3. **Payload Anatomy (`PayloadInspector.tsx` & `toolDictionary.ts`)**: In Educational Mode, when a known tool payload (e.g., `sqlmap -u ...`) is inspected, append an "Anatomy Room" section that breaks down the command flags into human-readable lessons. In Competition Mode, only show the raw code highlighter.

**Tech Stack:** React, TailwindCSS, Framer Motion, TypeScript, Lucide React.

---

### Task 1: UI State & Mode Switcher

**Files:**

- Modify: `ui/src/components/CommandCenter.tsx`

**Step 1: Write implementation**

Add `isEducationalMode` state to `CommandCenter`.

```tsx
const [isEducationalMode, setIsEducationalMode] = useState(false);
```

Add a toggle button to the top navigation bar (near the Node Analysis status or title):

```tsx
import { GraduationCap, Zap } from 'lucide-react';

{/* Mode Toggle Button */}
<button
    onClick={() => setIsEducationalMode(!isEducationalMode)}
    className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-bold transition-all ${
        isEducationalMode 
            ? 'bg-cyber-purple/20 border-cyber-purple/50 text-cyber-purple drop-shadow-[0_0_8px_rgba(112,0,255,0.4)]'
            : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
    }`}
>
    {isEducationalMode ? (
        <><GraduationCap className="w-3.5 h-3.5" /> EDU MODE</>
    ) : (
        <><Zap className="w-3.5 h-3.5" /> COMP MODE</>
    )}
</button>
```

Pass `isEducationalMode` to `OrchestratorChat` and `PayloadInspector`.

**Step 2: Commit**

```bash
git add ui/src/components/CommandCenter.tsx
git commit -m "feat(ui): add toggle for competition vs educational mode"
```

---

### Task 2: Thought Parser Utility

**Files:**

- Create: `ui/src/utils/thoughtParser.ts`
- Test: `tests/ui/test_thoughtParser.ts` (Manual Verification via Vite dev server)

**Step 1: Write minimal implementation**

```typescript
// ui/src/utils/thoughtParser.ts
export interface ParsedMessage {
    thought: string | null;
    content: string;
}

export function parseAgentMessage(rawContent: string): ParsedMessage {
    const thoughtMatch = rawContent.match(/<thought>([\s\S]*?)<\/thought>/);
    
    if (thoughtMatch) {
        return {
            thought: thoughtMatch[1].trim(),
            content: rawContent.replace(/<thought>[\s\S]*?<\/thought>/, '').trim()
        };
    }
    
    return {
        thought: null,
        content: rawContent.trim()
    };
}
```

**Step 2: Commit**

```bash
git add ui/src/utils/thoughtParser.ts
git commit -m "feat(ui): add parser utility for extracting agent thought blocks"
```

---

### Task 3: Thought Panel UI Component

**Files:**

- Create: `ui/src/components/chat/ThoughtPanel.tsx`

**Step 1: Write implementation**

```tsx
// ui/src/components/chat/ThoughtPanel.tsx
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
```

**Step 2: Commit**

```bash
git add ui/src/components/chat/ThoughtPanel.tsx
git commit -m "feat(ui): create collapsible brain panel for agent reasoning"
```

---

### Task 4: Integrate Thought Panel into Chat

**Files:**

- Modify: `ui/src/components/OrchestratorChat.tsx`

**Step 1: Modify props and chat loop**

Accept `isEducationalMode` prop:

```typescript
import { parseAgentMessage } from '../utils/thoughtParser';
import ThoughtPanel from './chat/ThoughtPanel';

interface OrchestratorChatProps {
    isEducationalMode?: boolean;
}
export default function OrchestratorChat({ isEducationalMode = false }: OrchestratorChatProps) {
// ...
```

Modify the mapping logic for Agent messages:

```tsx
// BEFORE
: 'bg-white/5 border-white/10 text-gray-400 italic text-[11px]'
}`}>
{msg.content}
<div className="mt-1 text-[9px] opacity-40 text-right">{msg.timestamp}</div>

// AFTER
: 'bg-white/5 border-white/10 text-gray-400 italic text-[11px]'
}`}>
{msg.type === 'agent' ? (
    <>
        {isEducationalMode && parseAgentMessage(msg.content).thought && (
            <ThoughtPanel thought={parseAgentMessage(msg.content).thought || ''} />
        )}
        <div className="whitespace-pre-wrap">{parseAgentMessage(msg.content).content}</div>
    </>
) : (
    msg.content
)}
<div className="mt-1 text-[9px] opacity-40 text-right">{msg.timestamp}</div>
```

**Step 2: Disable Backend Thought Stripping**

- Modify: `src/asas_agent/graph/workflow.py`
Wait, checking `workflow.py`, currently `clean_content = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL)` is used to strip thoughts before extracting tool calls.
However, the UI emitter fires inside `__main__.py` or the graph *after* the raw content is generated. Actually, the `orchestrator_message` in `workflow.py` or `__main__.py` might already be stripped.
Wait, let's verify `src/asas_agent/__main__.py`:
Line 193: `msg = value["messages"][-1]` which is the raw `AIMessage` returned by the LLM. So the `<thought>` tag *is* present in `msg.content` because `clean_content` in `workflow.py` just extracts tools, it doesn't mutate `msg.content`. No backend changes needed! The UI will receive the raw `<thought>...</thought>`.

**Step 3: Commit**

```bash
git add ui/src/components/OrchestratorChat.tsx
git commit -m "feat(ui): render conditional agent thoughts in chat feed"
```

---

### Task 5: Educational Payload Dictionary

**Files:**

- Create: `ui/src/utils/toolDictionary.ts`

**Step 1: Write static dictionary**

```typescript
// ui/src/utils/toolDictionary.ts

export interface ToolAnatomy {
    name: string;
    description: string;
    flags: Record<string, string>;
}

export const TOOL_DICTIONARY: Record<string, ToolAnatomy> = {
    'kali_sqlmap': {
        name: 'SQLMap (Automated SQL Injection)',
        description: 'An open source penetration testing tool that automates the process of detecting and exploiting SQL injection flaws.',
        flags: {
            '-u': 'Target URL to scan.',
            '--batch': 'Never ask for user input, use the default behavior.',
            '--dbs': 'Enumerate DBMS databases.',
            '--tables': 'Enumerate DBMS database tables.',
            '--dump': 'Dump DBMS database table entries.',
            '-D': 'DBMS database to enumerate.',
            '-T': 'DBMS database table to enumerate.'
        }
    },
    'kali_nmap': {
        name: 'Nmap (Network Mapper)',
        description: 'A free and open source utility for network discovery and security auditing.',
        flags: {
            '-p': 'Only scan specified ports.',
            '-sV': 'Probe open ports to determine service/version info.',
            '-sC': 'Equivalent to --script=default. Runs default NSE scripts.',
            '-T4': 'Set timing template (higher is faster).',
            '-Pn': 'Treat all hosts as online -- skip host discovery.'
        }
    },
    'kali_exec': {
         name: 'General Shell Execution',
         description: 'Executes a raw bash command directly in the Kali Linux VM. Used for standard Linux utilities.',
         flags: {}
    }
};

export function analyzePayload(toolName: string, args: Record<string, any>) {
    const knowledge = TOOL_DICTIONARY[toolName];
    if (!knowledge) return null;
    
    // Attempt to map passed arguments to known flags
    // This is a simplified heuristic
    const matchedFlags: Array<{ flag: string, meaning: string, value: string }> = [];
    
    if (args && typeof args === 'object') {
        const rawCommand = args.command || args.code || Object.values(args).join(' ');
        
        Object.entries(knowledge.flags).forEach(([flag, meaning]) => {
            if (typeof rawCommand === 'string' && rawCommand.includes(flag)) {
                matchedFlags.push({ flag, meaning, value: '' });
            }
        });
    }
    
    return {
        anatomy: knowledge,
        detected: matchedFlags
    };
}
```

**Step 2: Commit**

```bash
git add ui/src/utils/toolDictionary.ts
git commit -m "feat(ui): add ctf tool knowledge dictionary for payload anatomy"
```

---

### Task 6: Upgrade PayloadInspector

**Files:**

- Modify: `ui/src/components/PayloadInspector.tsx`

**Step 1: Add prop and implement Anatomy breakdown**

Accept `isEducationalMode` prop:

```typescript
import { analyzePayload } from '../utils/toolDictionary';
import { BookOpen } from 'lucide-react';

interface PayloadInspectorProps {
    node: Node | null;
    isEducationalMode?: boolean;
}
export default function PayloadInspector({ node, isEducationalMode = false }: PayloadInspectorProps) {
// ...
```

In the render function of `PayloadInspector.tsx`:

```tsx
const analysis = node ? analyzePayload(node.data.label, node.data.payload) : null;

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
```

**Step 2: Commit**

```bash
git add ui/src/components/PayloadInspector.tsx
git commit -m "feat(ui): render educational tool anatomy within payload inspector conditionally"
```
