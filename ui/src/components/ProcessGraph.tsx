"use client";

import React, { useCallback } from 'react';
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

const initialNodes: Node[] = [
    {
        id: 'start',
        position: { x: 50, y: 150 },
        data: { label: 'Target Acquired' },
        type: 'input',
        style: { background: '#00f2ff20', color: '#00f2ff', border: '1px solid #00f2ff50', borderRadius: '12px' }
    },
];

const initialEdges: Edge[] = [];

export default function ProcessGraph() {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge({
            ...params,
            animated: true,
            style: { stroke: '#7000ff' },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#7000ff' }
        }, eds)),
        [setEdges]
    );

    return (
        <div className="w-full h-full bg-[#0b0e14]">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                fitView
                className="cyber-graph"
            >
                <Background color="#1a1f26" gap={20} />
                <Controls showInteractive={false} className="glass-panel" />
                <MiniMap
                    nodeColor={(n) => (n.type === 'input' ? '#00f2ff' : '#7000ff')}
                    maskColor="rgba(11, 14, 20, 0.7)"
                    className="glass-panel rounded-xl"
                />
            </ReactFlow>
            <style jsx global>{`
        .react-flow__node {
          font-family: 'Inter', sans-serif;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          padding: 10px;
          box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
        }
        .react-flow__handle {
          background: #7000ff;
          width: 8px;
          height: 8px;
          border: 2px solid #0b0e14;
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
