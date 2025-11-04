"use client";
import { Badge, Tooltip } from "@mantine/core";
import { Handle, Position } from "@xyflow/react";
import styled from "styled-components";
import getBadgeColor from "../../app/utils/badge-colors";

const Container = styled.div`
  border: 1px solid #000;
  border-radius: 10px;
  padding: 24px 18px;
  gap: 16px;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  color: #000;
  width: 400px;
  cursor: pointer;

  &:hover {
    background-color: ${({ theme }) => theme.colors.gray[100] || "#f0f0f0"};
  }
`;

const ReasonContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const TagContainer = styled.div`
  display: flex;
  gap: 4px;
`;

const TooltipContent = ({ reasons }: { reasons: string[] }) => {
  return (
    <ReasonContainer>
      {reasons.map((reason) => (
        <span key={reason}>{reason}</span>
      ))}
    </ReasonContainer>
  );
};

export default function DocumentNode({
  data,
}: {
  data: { label: string; url: string; reasons: string[]; tags: string[] };
}) {
  const handleClick = () => {
    console.log("Clicked on node:", data.label);
    console.log("Opening URL:", data.url);
    window.open(data.url, "_blank", "noopener,noreferrer");
  };

  return (
    <Container onClick={handleClick}>
      <Handle type="target" position={Position.Left} id="a" />
      <span>
        <b>{data.label}</b>
      </span>
      <TagContainer>
        {data.tags.map((tag) => (
          <Badge variant="gradient" gradient={getBadgeColor(tag)} size="sm" key={tag}>
            {tag}
          </Badge>
        ))}
      </TagContainer>
      <Handle type="source" position={Position.Right} id="b" />
    </Container>
  );
}
