import { useMemo } from 'react';
import { Node, Edge } from 'reactflow';
import { AgentEvent } from './useAgentEvents';

export interface GraphData {
    nodes: Node[];
    edges: Edge[];
    stepData: Record<string, unknown>;
}

export function useGraphData(events: AgentEvent[]): GraphData {
    return useMemo(() => {
        // Initial state for orchestrator and known workers
        const nodes: Node[] = [
            {
                id: 'orchestrator',
                type: 'agent',
                position: { x: 250, y: 50 },
                data: {
                    label: 'ReAct Orchestrator',
                    agentType: 'orchestrator',
                    status: 'running',
                    details: 'Awaiting instructions'
                }
            },
            {
                id: 'web_agent',
                type: 'agent',
                position: { x: 100, y: 200 },
                data: {
                    label: 'Web Agent',
                    agentType: 'worker',
                    status: 'pending',
                    details: 'Awaiting tasks'
                }
            },
            {
                id: 'crypto_agent',
                type: 'agent',
                position: { x: 400, y: 200 },
                data: {
                    label: 'Crypto Agent',
                    agentType: 'worker',
                    status: 'pending',
                    details: 'Awaiting tasks'
                }
            }
        ];

        const edges: Edge[] = [
            {
                id: 'e-orch-web',
                source: 'orchestrator',
                target: 'web_agent',
                animated: false,
                style: { stroke: '#334155', strokeWidth: 1, strokeDasharray: '5 5' }
            },
            {
                id: 'e-orch-crypto',
                source: 'orchestrator',
                target: 'crypto_agent',
                animated: false,
                style: { stroke: '#334155', strokeWidth: 1, strokeDasharray: '5 5' }
            }
        ];

        const stepData: Record<string, unknown> = {};

        // Track the current active node to attach edges to tools
        const currentWorkerId = 'web_agent'; // default guess
        let toolNodeY = 350;

        events.forEach(event => {
            const data = event.data as Record<string, unknown>;
            const timestamp = event.timestamp.toString();

            // 1. Agent Thought/Action
            if (event.type === 'orchestrator_message') {
                const thought = data.content as string;
                if (thought) {
                    const orchNode = nodes.find(n => n.id === 'orchestrator');
                    if (orchNode) {
                        orchNode.data.status = 'running';
                        orchNode.data.details = 'Thinking / Delegating';
                    }
                }

                const toolCalls = data.tool_calls as Array<{ name: string, args: Record<string, unknown> }>;
                if (toolCalls && toolCalls.length > 0) {
                    const toolName = toolCalls[0].name;

                    // Activate worker line
                    const workerNode = nodes.find(n => n.id === currentWorkerId);
                    if (workerNode) {
                        workerNode.data.status = 'running';
                        workerNode.data.details = `Executing ${toolName}`;
                    }

                    const edgeToWorker = edges.find(e => e.target === currentWorkerId);
                    if (edgeToWorker) {
                        edgeToWorker.animated = true;
                        edgeToWorker.style = { stroke: '#00f2ff', strokeWidth: 2 };
                    }

                    // Create Tool Node
                    const toolNodeId = `tool_${timestamp}`;
                    nodes.push({
                        id: toolNodeId,
                        type: 'agent',
                        position: { x: 100, y: toolNodeY }, // Stack them down
                        data: {
                            label: `Tool: ${toolName}`,
                            agentType: 'system',
                            status: 'running',
                            details: `Invoked with arguments`
                        }
                    });

                    // Edge from worker to tool
                    edges.push({
                        id: `e-${currentWorkerId}-${toolNodeId}`,
                        source: currentWorkerId,
                        target: toolNodeId,
                        animated: true,
                        style: { stroke: '#7000ff', strokeWidth: 2 }
                    });

                    // Save payload data for the inspector
                    stepData[toolNodeId] = {
                        title: toolName,
                        payload: `${toolName} ${JSON.stringify(toolCalls[0].args)}`,
                        logs: 'Executing...',
                        conclusion: 'Pending...'
                    };

                    toolNodeY += 150;
                }
            }

            // 2. Tool Execution Result
            else if (event.type === 'tool_result') {
                // Find the latest running tool node
                const toolNodes = nodes.filter(n => n.data.agentType === 'system' && n.data.status === 'running');
                const lastToolNode = toolNodes[toolNodes.length - 1];

                if (lastToolNode) {
                    const isError = data.is_error;
                    lastToolNode.data.status = isError ? 'error' : 'success';
                    lastToolNode.data.details = isError ? 'Execution failed' : 'Execution succeeded';

                    const edgeToTool = edges.find(e => e.target === lastToolNode.id);
                    if (edgeToTool) {
                        edgeToTool.animated = false;
                        edgeToTool.style = { stroke: isError ? '#f43f5e' : '#10b981', strokeWidth: 2 };
                    }

                    // Update step data
                    if (stepData[lastToolNode.id]) {
                        stepData[lastToolNode.id].logs = data.content;
                        stepData[lastToolNode.id].conclusion = isError ? 'Tool execution encountered an error.' : 'Tool returned successfully.';
                    }
                }
            }

            // 3. System Messages (Finish/Error)
            else if (event.type === 'system_message') {
                if (data.level === 'warning' && (data.content as string).includes('Terminated')) {
                    nodes.forEach(n => {
                        if (n.data.agentType === 'orchestrator' || n.data.agentType === 'worker') {
                            n.data.status = 'success';
                            if (n.data.agentType === 'orchestrator') n.data.details = 'Analysis Complete';
                            if (n.data.agentType === 'worker') n.data.details = 'Task Complete';
                        }
                    });
                    edges.forEach(e => { e.animated = false; });
                }
            }
        });

        return { nodes, edges, stepData };
    }, [events]);
}
