"use client";

import React, { useCallback, useState } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    addEdge,
    MarkerType,
    Node,
    Edge,
    Connection
} from 'reactflow';
import 'reactflow/dist/style.css';
import 'reactflow/dist/style.css';
import AgentNode from './graph/AgentNode';
import { AgentEvent } from '../hooks/useAgentEvents';
import { useGraphData } from '../hooks/useGraphData';

const nodeTypes = {
    agent: AgentNode,
};

const initialNodes: Node[] = [
    {
        id: '1',
        type: 'agent',
        position: { x: 250, y: 50 },
        data: {
            label: 'ReAct Orchestrator',
            agentType: 'orchestrator',
            status: 'success',
            details: 'Delegating to Web Agent'
        }
    },
    {
        id: '2',
        type: 'agent',
        position: { x: 100, y: 200 },
        data: {
            label: 'Web Agent',
            agentType: 'worker',
            status: 'running',
            details: 'Executing nmap -sV target'
        }
    },
    {
        id: '3',
        type: 'agent',
        position: { x: 400, y: 200 },
        data: {
            label: 'Crypto Agent',
            agentType: 'worker',
            status: 'pending',
            details: 'Awaiting tasks'
        }
    },
    {
        id: '4',
        type: 'agent',
        position: { x: 100, y: 350 },
        data: {
            label: 'Tool Execution',
            agentType: 'system',
            status: 'error',
            details: 'Connection refused on port 80'
        }
    }
];

const initialEdges: Edge[] = [
    {
        id: 'e1-2',
        source: '1',
        target: '2',
        animated: true,
        style: { stroke: '#00f2ff', strokeWidth: 2 }
    },
    {
        id: 'e1-3',
        source: '1',
        target: '3',
        animated: false,
        style: { stroke: '#334155', strokeWidth: 1, strokeDasharray: '5 5' }
    },
    {
        id: 'e2-4',
        source: '2',
        target: '4',
        animated: true,
        style: { stroke: '#f43f5e', strokeWidth: 2 }
    }
];

interface ProcessGraphProps {
    events?: AgentEvent[];
    onNodeSelect?: (nodeId: string | null) => void;
}

export default function ProcessGraph({ events = [], onNodeSelect }: ProcessGraphProps) {
    const { nodes: derivedNodes, edges: derivedEdges } = useGraphData(events);

    const [nodes, setNodes, onNodesChange] = useNodesState(derivedNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(derivedEdges);

    // Sync state when derived data changes
    React.useEffect(() => {
        setNodes(derivedNodes);
        setEdges(derivedEdges);
    }, [derivedNodes, derivedEdges, setNodes, setEdges]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge({
            ...params,
            animated: true,
            style: { stroke: '#7000ff', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#7000ff' }
        }, eds)),
        [setEdges]
    );

    const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        if (onNodeSelect) {
            onNodeSelect(node.id);
        }
    }, [onNodeSelect]);

    const handlePaneClick = useCallback(() => {
        if (onNodeSelect) {
            onNodeSelect(null);
        }
    }, [onNodeSelect]);

    return (
        <div className="w-full h-full bg-[#0b0e14]">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={handleNodeClick}
                onPaneClick={handlePaneClick}
                nodeTypes={nodeTypes}
                fitView
                className="cyber-graph"
                defaultEdgeOptions={{
                    style: { stroke: '#7000ff', strokeWidth: 2 },
                    markerEnd: { type: MarkerType.ArrowClosed, color: '#7000ff' }
                }}
            >
                <Background color="#1a1f26" gap={20} size={2} />
                <Controls showInteractive={false} className="glass-panel" />
                <MiniMap
                    nodeColor={(n) => {
                        if (n.data?.status === 'running') return '#00f2ff';
                        if (n.data?.status === 'success') return '#10b981';
                        if (n.data?.status === 'error') return '#f43f5e';
                        return '#64748b';
                    }}
                    maskColor="rgba(11, 14, 20, 0.7)"
                    className="glass-panel rounded-xl"
                />
            </ReactFlow>
            <style jsx global>{`
                /* Cyberpunk animated edge (flowing dash effect) */
                .react-flow__edge-path {
                    stroke-dasharray: 10;
                    animation: dashdraw 1s linear infinite;
                }
                
                @keyframes dashdraw {
                    from { stroke-dashoffset: 20; }
                    to { stroke-dashoffset: 0; }
                }

                .react-flow__controls button {
                    background: rgba(255, 255, 255, 0.05);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                    color: #94a3b8;
                }
                .react-flow__controls button:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: white;
                }
            `}</style>
        </div>
    );
}
