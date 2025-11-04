"use client";
import { Edge, Node, OnEdgesChange, OnNodesChange, ReactFlow } from "@xyflow/react";
import { Controls } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { on } from "events";
import DocumentNode from "./DocumentNode";
import InitialNode from "./InitialNode";
import MindmapContent from "./MindmapContent";
import ReasonNode from "./ReasonNode";

const nodeTypes = {
  document: DocumentNode,
  initial: InitialNode,
  reason: ReasonNode,
};

export default function Mindmap({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onLayout,
}: {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange<Node>;
  onEdgesChange: OnEdgesChange<Edge>;
  onLayout: () => void;
}) {
  return (
    <ReactFlow
      fitView
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
    >
      <MindmapContent />

      <Controls position="bottom-left">
        <button
          style={{
            background: "#F2F2F2",
            border: "1px solid #ccc",
            borderRadius: "4px",
            padding: "0px",
            marginLeft: "0px",
            cursor: "pointer",
            color: "black",
          }}
          onClick={() => {
            onLayout();
          }}
        >
          R
        </button>
      </Controls>
    </ReactFlow>
  );
}
