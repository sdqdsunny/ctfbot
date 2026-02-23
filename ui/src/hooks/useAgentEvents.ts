import { useEffect, useState } from 'react';

export interface AgentEvent {
    type: string;
    data: Record<string, unknown>;
    timestamp: number;
}

export function useAgentEvents() {
    const [events, setEvents] = useState<AgentEvent[]>([]);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8765/ws');

        ws.onmessage = (event) => {
            try {
                const parsed = JSON.parse(event.data);
                if (parsed.type !== 'ack') {
                    setEvents(prev => [...prev, {
                        ...parsed,
                        timestamp: Date.now()
                    }]);
                }
            } catch (e) {
                console.error("Failed to parse WS message", e);
            }
        };

        return () => ws.close();
    }, []);

    return events;
}
