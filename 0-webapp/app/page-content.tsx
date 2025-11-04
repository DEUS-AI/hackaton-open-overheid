"use client";
import { useVoiceAssistant } from "@livekit/components-react";
import { Edge, Node, useEdges, useEdgesState, useNodesState, useReactFlow } from "@xyflow/react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import styled from "styled-components";
import TranscriptionView from "../components/TranscriptionView";
// Assets movidos a /public/assets, reemplazamos imports SVGR por <img />
// import LogoIcon from "./assets/logo.svg";
// import SeparatorIcon from "./assets/separator.svg";
import MainInput from "../components/MainInput";
import VoiceTooltipContent from "../components/VoiceTooltipContent";
import Mindmap from "../components/mindmap/Mindmap";
import MindmapTransformer, { reorganizePositions } from "./utils/mindmap-transformer";
import { MindmapData } from "./utils/types";

const Nav = styled.nav`
  position: sticky;
  height: 77px;
  top: 0;
  left: 0;
  width: 100%;
  padding: 20px;
  background-color: ${({ theme }) => theme.colors.primary};
  text-align: left;
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 16px;
`;

const Container = styled.div`
  display: flex;
  width: 100%;
  height: 100%;
  justify-content: center;
  /* align-items: center; */
`;

const Heading = styled.h1`
  color: ${({ theme }) => theme.colors.primary};
  font-size: 32px;
  font-weight: 800;
  text-align: center;
`;

const InnerContainerLeft = styled.div<{
  $haveMindmap: boolean;
  $isVoiceActive: boolean;
  $showVoiceBubble: boolean;
}>`
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  margin-top: auto;
  width: 25%;
  height: 100%;
  max-height: calc(100vh - 77px);
  ${({ $haveMindmap }) =>
    !$haveMindmap &&
    `
    width: 75%;
    max-width: 1024px;
    gap: 48px;
    margin-top: 200px;
    justify-content: flex-start;
    ;
  `}
  ${({ $isVoiceActive, $showVoiceBubble }) =>
    $isVoiceActive &&
    $showVoiceBubble &&
    `
    margin-top: 32px;
  `}

${({ $isVoiceActive, $haveMindmap, $showVoiceBubble }) =>
    $isVoiceActive &&
    $haveMindmap &&
    $showVoiceBubble &&
    `
    margin-top: 0;
  `}
`;

const InnerContainerRight = styled.div`
  width: 65%;
  display: flex;
  flex-grow: 1;
`;

const Separator = styled.div`
  width: 2%;
  background: linear-gradient(
    180deg,
    ${({ theme }) => theme.colors.primary},
    ${({ theme }) => theme.colors.secondary} 150%
  );
`;

interface PageContentProps {
  onConnectButtonClicked: () => void;
  onVoiceActivation: (isVoiceActive: boolean) => void;
  mindmapData: MindmapData | undefined;
}

const PageContent: React.FC<PageContentProps> = ({
  onConnectButtonClicked,
  onVoiceActivation,
  mindmapData,
}) => {
  const { agentTranscriptions, state: agentState } = useVoiceAssistant();
  const { t } = useTranslation();
  const [isLayouted, setIsLayouted] = useState(false);
  const [showVoiceBubble, setShowVoiceBubble] = useState(false);

  const [finalNodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [finalEdges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [isVoiceActive, setIsVoiceActive] = useState(false);

  useEffect(() => {
    if (!mindmapData) return;

    const { nodes, edges } = MindmapTransformer(mindmapData);

    setNodes(nodes);
    setEdges(edges);
  }, [mindmapData, setNodes, setEdges]);

  const onLayout = useCallback(() => {
    const layouted = reorganizePositions(finalNodes, finalEdges);

    setNodes([...layouted.nodes]);
    setEdges([...layouted.edges]);
  }, [finalEdges, finalNodes]);

  useEffect(() => {
    if (finalNodes.length > 0 && finalNodes[0].measured && !isLayouted) {
      onLayout();
      setIsLayouted(true);
    }
  }, [finalNodes, isLayouted, onLayout]);

  useEffect(() => {
    // Consider voice active if agentTranscriptions is not empty
    setIsVoiceActive(agentTranscriptions.length > 0);
  }, [agentTranscriptions, onVoiceActivation]);

  return (
    <>
      <Container>
        <InnerContainerLeft
          $haveMindmap={!!mindmapData}
          $isVoiceActive={agentState !== "disconnected"}
          $showVoiceBubble={showVoiceBubble}
        >
          {showVoiceBubble && agentState !== "disconnected" && <VoiceTooltipContent />}
          {showVoiceBubble && <TranscriptionView hasMindmapData={!!mindmapData} />}
          {!mindmapData && !showVoiceBubble && <Heading>{t("heading")}</Heading>}

          <MainInput
            onConnectButtonClicked={onConnectButtonClicked}
            onVoiceActivation={onVoiceActivation}
            haveMindmapData={!!mindmapData}
            setShowVoiceBubble={setShowVoiceBubble}
          />
        </InnerContainerLeft>
        {mindmapData && (
          <>
            <Separator />
            <InnerContainerRight>
              <Mindmap
                nodes={finalNodes}
                edges={finalEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onLayout={onLayout}
              />
            </InnerContainerRight>
          </>
        )}
      </Container>
    </>
  );
};

export default PageContent;
