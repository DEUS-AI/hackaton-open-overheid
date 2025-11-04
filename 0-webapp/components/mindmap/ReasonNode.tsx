"use client";
import { Handle, Position } from "@xyflow/react";
import styled from "styled-components";

const Container = styled.div`
  border: 1px solid #000;
  border-radius: 10px;
  padding: 10px;
  background-color: #fff;
  color: #000;

  min-width: 500px;
`;

export default function ReasonNode({ data }: { data: { label: string[] } }) {
  return (
    <Container>
      <Handle type="target" position={Position.Left} id="a" />
      <ul>
        {data.label.map((label) => (
          <li key={label}>{label}</li>
        ))}
      </ul>
    </Container>
  );
}
