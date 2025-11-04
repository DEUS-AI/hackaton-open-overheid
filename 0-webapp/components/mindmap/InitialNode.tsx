"use client";
import { Handle, Position } from "@xyflow/react";
import styled from "styled-components";

const Container = styled.div`
  border: 1px solid #000;
  border-radius: 12px;
  padding: 12px 24px;
  background-color: rgb(21, 58, 102, 0.15);
  color: #000;
  text-align: center;
  font-style: italic;

  max-width: 175px;
`;

export default function InitialNode({ data }: { data: { label: string } }) {
  return (
    <Container>
      <span>{data.label}</span>
      <Handle type="source" position={Position.Right} id="a" />
    </Container>
  );
}
