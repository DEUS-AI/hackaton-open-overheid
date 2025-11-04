"use client";
import { useRoomContext, useVoiceAssistant } from "@livekit/components-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { TextInput, ActionIcon, Group, rem, Paper, Tooltip } from "@mantine/core";
import { IconMicrophone, IconMicrophoneOff, IconArrowUp, IconWaveSine, IconArrowRight } from "@tabler/icons-react";

interface MainInputProps {
  onConnectButtonClicked: () => void;
  onVoiceActivation: (isVoiceActive: boolean) => void;
  haveMindmapData: boolean;
  setShowVoiceBubble: (showVoiceBubble: boolean) => void;
}

const MainInput: React.FC<MainInputProps> = ({
  onConnectButtonClicked,
  onVoiceActivation,
  haveMindmapData,
  setShowVoiceBubble,
}) => {
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const { state: agentState } = useVoiceAssistant();
  const { localParticipant } = useRoomContext();

  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const { t } = useTranslation();

  const onMute = useCallback(() => {
    localParticipant.setMicrophoneEnabled(!localParticipant.isMicrophoneEnabled);
  }, [localParticipant]);

  const onVoiceActivationClick = useCallback(() => {
    if (agentState === "disconnected") {
      onConnectButtonClicked();
    }
    onVoiceActivation(!isVoiceActive);
    setShowVoiceBubble(!isVoiceActive);
  }, [agentState, isVoiceActive, onConnectButtonClicked, onVoiceActivation]);

  // Uncomment this to connect to the room when the app is mounted
  useEffect(() => {
    onConnectButtonClicked();
  }, [onConnectButtonClicked]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    e.stopPropagation();
    console.log("Sending text...");
    if (input === "") return;

    localParticipant
      .sendText(input, { topic: "custom_topic" })
      .then((v) => console.log("sent success", v))
      .catch((e) => console.log("error sent", e));
  };

  return (
    <form onSubmit={handleSubmit} style={{ width: "100%" }}>
      <Paper
        withBorder={!haveMindmapData}
        radius={haveMindmapData ? 0 : "xl"}
        py={haveMindmapData ? "xs" : "sm"}
        px={haveMindmapData ? "sm" : "md"}
        style={{
          borderTop: haveMindmapData
            ? `${rem(3)} solid var(--mantine-color-govBlue-filled)`
            : undefined,
          borderWidth: haveMindmapData ? undefined : rem(3),
          borderColor: isFocused && !haveMindmapData ? "#153A66" : undefined,
          boxShadow: isFocused && !haveMindmapData ? `0 0 0 2px #153A6622` : undefined,
          display: "flex",
          alignItems: "center",
          gap: rem(8),
          transition: "border-color 0.2s, box-shadow 0.2s"
        }}
      >
        <TextInput
          placeholder={t("input.placeholder")}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          flex={1}
          rightSectionWidth={0}
          styles={{
            input: {
              paddingTop: rem(10),
              paddingBottom: rem(10),
              fontSize: rem(18),
              fontStyle: "italic",
              border: "0px"
            },
          }}
        />
        <Group gap={4} wrap="nowrap">
          <Tooltip 
            label={localParticipant.isMicrophoneEnabled ? t("tooltips.microphone") : t("tooltips.microphoneOff")}
            position="top"
          >
            <ActionIcon
              variant="subtle"
              color="govGray"
              size="lg"
              aria-label="mute"
              onClick={() => onMute()}
            >
              {localParticipant.isMicrophoneEnabled ? <IconMicrophone size={20} /> : <IconMicrophoneOff size={20} />}
            </ActionIcon>
          </Tooltip>
          <Tooltip 
            label={isVoiceActive ? t("tooltips.voiceActive") : t("tooltips.voiceActivation")}
            position="top"
          >
            <ActionIcon
              variant={isVoiceActive ? "filled" : "light"}
              color={isVoiceActive ? "govBlue" : "govGray"}
              size="lg"
              aria-label="voice"
              onClick={() => onVoiceActivationClick()}
            >
              <IconWaveSine size={22} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label={t("tooltips.send")} position="top">
            <ActionIcon type="submit" variant="filled" color="govBlue" size="lg" aria-label="send">
              <IconArrowRight size={20} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Paper>
    </form>
  );
};

export default MainInput;
