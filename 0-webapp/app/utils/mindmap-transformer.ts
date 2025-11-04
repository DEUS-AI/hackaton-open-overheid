import Dagre from "@dagrejs/dagre";
import { Edge, Node } from "@xyflow/react";
import { Document, MindmapData } from "./types";

function getInitialNode(summary: string): Node {
  return {
    id: "initial",
    position: { x: 0, y: 0 },
    data: { label: summary },
    type: "initial",
  };
}

function getDocumentNode(document: Document, offset: number): Node {
  return {
    id: document.id,
    position: { x: 500, y: offset * 100 },
    data: {
      label: document.name,
      url: document.link,
      reasons: document.reasons,
      tags: document.tags,
    },
    type: "document",
  };
}

function getReasonsNode(reason: string[], docOffset: number, docId: string): Node {
  return {
    id: `${docId}-reasons`,
    position: { x: 1500, y: docOffset * 100 },
    data: { label: reason },
    type: "reason",
  };
}

export function reorganizePositions(
  nodes: Node[],
  edges: Edge[]
): { nodes: Node[]; edges: Edge[] } {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", align: "DR", nodesep: 50, ranksep: 150 });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) =>
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    })
  );

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - (node.measured?.width ?? 0) / 2;
      const y = position.y - (node.measured?.height ?? 0) / 2;

      return { ...node, position: { x, y } };
    }),
    edges,
  };
}

export default function MindmapTransformer(data: MindmapData): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  nodes.push(getInitialNode(data.summary));

  data.documents.forEach((document, index) => {
    nodes.push(getDocumentNode(document, index));
    nodes.push(getReasonsNode(document.reasons, index, document.id));
    edges.push({
      id: `edge-${document.id}-reasons`,
      source: document.id,
      target: `${document.id}-reasons`,
    });
    edges.push({
      id: `edge-${document.id}-${index}`,
      source: "initial",
      target: document.id,
      label: (document.confidence * 100).toFixed(2) + "%",
      animated: true,
    });
  });

  return reorganizePositions(nodes, edges);
}
