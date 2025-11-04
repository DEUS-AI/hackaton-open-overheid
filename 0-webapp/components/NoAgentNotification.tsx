"use client";
import type { AgentState } from "@livekit/components-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Notification, Anchor, ActionIcon, rem } from "@mantine/core";
import { IconAlertTriangle, IconX } from "@tabler/icons-react";

interface NoAgentNotificationProps extends React.PropsWithChildren<object> {
  state: AgentState;
}

/**
 * Renders some user info when no agent connects to the room after a certain time.
 */
export function NoAgentNotification(props: NoAgentNotificationProps) {
  const timeToWaitMs = 10_000;
  const timeoutRef = useRef<number | null>(null);
  const [showNotification, setShowNotification] = useState(false);
  const agentHasConnected = useRef(false);
  const { t } = useTranslation();

  // If the agent has connected, we don't need to show the notification.
  if (
    ["listening", "thinking", "speaking"].includes(props.state) &&
    agentHasConnected.current == false
  ) {
    agentHasConnected.current = true;
  }

  useEffect(() => {
    if (props.state === "connecting") {
      timeoutRef.current = window.setTimeout(() => {
        if (props.state === "connecting" && agentHasConnected.current === false) {
          setShowNotification(true);
        }
      }, timeToWaitMs);
    } else {
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
      setShowNotification(false);
    }

    return () => {
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, [props.state]);

  return (
    <>
      {showNotification ? (
        <Notification
          withCloseButton={false}
          radius="md"
          icon={<IconAlertTriangle size={20} />}
          style={{
            position: "fixed",
            top: rem(24),
            left: "50%",
            transform: "translateX(-50%)",
            maxWidth: "90vw",
            display: "flex",
            alignItems: "center",
            gap: rem(8),
          }}
        >
          <span style={{ whiteSpace: "nowrap" }}>{t("noAgent.message")}</span>{" "}
          <Anchor
            href="https://docs.livekit.io/agents/quickstarts/s2s/"
            target="_blank"
            underline="always"
            style={{ whiteSpace: "nowrap" }}
          >
            {t("noAgent.viewGuide")}
          </Anchor>
          <ActionIcon
            variant="subtle"
            aria-label="close"
            onClick={() => setShowNotification(false)}
            ml="xs"
          >
            <IconX size={16} />
          </ActionIcon>
        </Notification>
      ) : null}
    </>
  );
}
