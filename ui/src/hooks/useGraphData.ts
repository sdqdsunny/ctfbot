import { useMemo } from 'react';
import { Node, Edge } from 'reactflow';
import { AgentEvent } from './useAgentEvents';

export interface StepInfo {
    title: string;
    payload: string;
    logs: string;
    conclusion: string;
}

export interface GraphData {
    nodes: Node[];
    edges: Edge[];
    stepData: Record<string, StepInfo>;
}

export function useGraphData(events: AgentEvent[]): GraphData {
    return useMemo(() => {
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

        const stepData: Record<string, StepInfo> = {};
        const currentWorkerId = 'web_agent';
        let toolNodeY = 350;

        // Accumulate logs per worker
        const workerLogs: Record<string, string[]> = {};
        const workerPayloads: Record<string, string[]> = {};

        events.forEach(event => {
            const data = event.data as Record<string, unknown>;
            const timestamp = event.timestamp.toString();

            if (event.type === 'orchestrator_message') {
                const thought = data.content as string;
                if (thought) {
                    const orchNode = nodes.find(n => n.id === 'orchestrator');
                    if (orchNode) {
                        orchNode.data.status = 'running';
                        orchNode.data.details = 'Thinking / Delegating';
                    }
                    stepData['orchestrator'] = {
                        title: 'ReAct Orchestrator',
                        payload: '',
                        logs: thought,
                        conclusion: thought.substring(0, 200)
                    };
                }

                const toolCalls = data.tool_calls as Array<{ name: string, args: Record<string, unknown> }>;
                if (toolCalls && toolCalls.length > 0) {
                    const toolName = toolCalls[0].name;
                    const payloadStr = `${toolName} ${JSON.stringify(toolCalls[0].args)}`;

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

                    const toolNodeId = `tool_${timestamp}`;
                    nodes.push({
                        id: toolNodeId,
                        type: 'agent',
                        position: { x: 100, y: toolNodeY },
                        data: {
                            label: `Tool: ${toolName}`,
                            agentType: 'system',
                            status: 'running',
                            details: 'Invoked with arguments'
                        }
                    });

                    edges.push({
                        id: `e-${currentWorkerId}-${toolNodeId}`,
                        source: currentWorkerId,
                        target: toolNodeId,
                        animated: true,
                        style: { stroke: '#7000ff', strokeWidth: 2 }
                    });

                    stepData[toolNodeId] = {
                        title: toolName,
                        payload: payloadStr,
                        logs: 'Executing...',
                        conclusion: 'Pending...'
                    };

                    if (!workerPayloads[currentWorkerId]) workerPayloads[currentWorkerId] = [];
                    workerPayloads[currentWorkerId].push(payloadStr);

                    stepData[currentWorkerId] = {
                        title: `Web Agent - ${toolName}`,
                        payload: workerPayloads[currentWorkerId].join('\n'),
                        logs: workerLogs[currentWorkerId]?.join('\n---\n') || 'Executing tools...',
                        conclusion: `Executing ${toolName} against target`
                    };

                    toolNodeY += 150;
                }
            }

            else if (event.type === 'tool_result') {
                const toolNodes = nodes.filter(n => n.data.agentType === 'system' && n.data.status === 'running');
                const lastToolNode = toolNodes[toolNodes.length - 1];
                const content = String(data.content);
                const isError = Boolean(data.is_error);

                if (lastToolNode) {
                    lastToolNode.data.status = isError ? 'error' : 'success';
                    lastToolNode.data.details = isError ? 'Execution failed' : 'Execution succeeded';

                    const edgeToTool = edges.find(e => e.target === lastToolNode.id);
                    if (edgeToTool) {
                        edgeToTool.animated = false;
                        edgeToTool.style = { stroke: isError ? '#f43f5e' : '#10b981', strokeWidth: 2 };
                    }

                    const toolStep = stepData[lastToolNode.id];
                    if (toolStep) {
                        toolStep.logs = content;
                        toolStep.conclusion = isError ? 'Tool execution encountered an error.' : 'Tool returned successfully.';
                    }
                }

                if (!workerLogs[currentWorkerId]) workerLogs[currentWorkerId] = [];
                workerLogs[currentWorkerId].push(content);

                stepData[currentWorkerId] = {
                    title: 'Web Agent',
                    payload: workerPayloads[currentWorkerId]?.join('\n') || '',
                    logs: workerLogs[currentWorkerId].join('\n---\n'),
                    conclusion: isError ? 'Some tools encountered errors.' : 'Tools executed successfully.'
                };
            }

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
