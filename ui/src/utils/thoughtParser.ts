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
