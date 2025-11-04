import { BarVisualizer, RoomAudioRenderer, useVoiceAssistant } from "@livekit/components-react";
import { Box } from "@mantine/core";

export default function VoiceTooltipContent() {
  const { state: agentState, audioTrack } = useVoiceAssistant();

  return (
    <Box style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <RoomAudioRenderer />
      <div style={{ height: 120, width: 240 }}>
        <BarVisualizer
          state={agentState}
          barCount={8}
          trackRef={audioTrack}
          className="agent-visualizer"
          options={{ minHeight: 24 }}
        />
      </div>
    </Box>
  );
}
