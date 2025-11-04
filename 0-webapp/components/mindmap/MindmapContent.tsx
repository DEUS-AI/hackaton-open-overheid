"use client";
import { Controls, useReactFlow } from "@xyflow/react";
import { Background, BackgroundVariant, MiniMap, Panel } from "@xyflow/react";
import { useEffect } from "react";

export default function MindmapContent() {
  const { fitBounds, getNodesBounds } = useReactFlow();
  const initialNodeBounds = getNodesBounds(["initial"]);

  useEffect(() => {
    fitBounds(
      {
        ...initialNodeBounds,
        x: initialNodeBounds.x + 700,
      },
      {
        duration: 1500,
        padding: 10,
      }
    );
  }, [fitBounds, initialNodeBounds.x, initialNodeBounds.y]);

  return (
    <>
      <Controls showInteractive={false} />
      <Panel position="top-left">
        <span style={{ color: "black" }}>DEUS Document Finder Mind Map</span>
      </Panel>
      <MiniMap />
      <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
    </>
  );
}
