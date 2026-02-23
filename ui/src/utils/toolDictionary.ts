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

export function analyzePayload(toolName: string, args: Record<string, unknown>) {
    const knowledge = TOOL_DICTIONARY[toolName];
    if (!knowledge) return null;

    // Attempt to map passed arguments to known flags
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
