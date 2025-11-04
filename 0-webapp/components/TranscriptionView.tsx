"use client";
import useCombinedTranscriptions from "@/hooks/useCombinedTranscriptions";
import * as React from "react";
import { ScrollArea, Stack, Paper, rem } from "@mantine/core";

interface TranscriptionViewProps {
  hasMindmapData: boolean;
}

export default function TranscriptionView({ hasMindmapData }: TranscriptionViewProps) {
  const combinedTranscriptions = useCombinedTranscriptions();
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [combinedTranscriptions]);

  return (
    <ScrollArea.Autosize
      mah={hasMindmapData ? "100%" : 400}
      style={{
        width: hasMindmapData ? "25vw" : "100%",
        maxWidth: hasMindmapData ? undefined : 1024,
        margin: "0 auto",
        position: "relative",
      }}
    >
      <Stack ref={containerRef} gap="sm" p="md" style={{ fontSize: rem(16), fontWeight: 500 }}>
        {combinedTranscriptions.map((segment) => (
          <Paper
            key={segment.id}
            shadow="xs"
            p="sm"
            radius="xl"
            style={{
              maxWidth: "80%",
              alignSelf: segment.role === "assistant" ? "flex-start" : "flex-end",
              color: "black",
              borderColor: segment.role === "assistant" ? "#E0E0E0" : "brand",
              borderWidth: rem(2),
              borderStyle: "solid",
              backgroundColor: segment.role === "assistant" ? "#F9F9F9" : "#8dbafd",
            }}
          >
            {segment.text}
          </Paper>
        ))}
      </Stack>
    </ScrollArea.Autosize>
  );
}
