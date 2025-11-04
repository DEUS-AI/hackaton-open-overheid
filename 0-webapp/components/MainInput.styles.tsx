import { css, styled } from "styled-components";

export const Container = styled.div<{ $haveMindmapData: boolean }>`
  display: flex;
  align-items: center;
  gap: 10px;
  border-radius: 30px;
  border: 3px solid ${({ theme }) => theme.colors.primary};
  padding-right: 10px;
  background-color: ${({ theme }) => theme.colors.background};
  width: 100%;
  color: ${({ theme }) => theme.colors.text};
  ${({ $haveMindmapData }) =>
    $haveMindmapData &&
    css`
      border: none;
      border-top: 3px solid ${({ theme }) => theme.colors.primary};
      border-radius: 0;
    `}
`;

export const Input = styled.input<{ $haveMindmapData: boolean }>`
  width: 100%;
  padding: 10px 40px;
  background-color: transparent;
  border: none;
  outline: none;

  font-size: 20px;
  font-style: italic;
  font-weight: 400;
  line-height: 150%; /* 30px */
  ${({ $haveMindmapData }) =>
    $haveMindmapData &&
    css`
      padding: 10px 16px;
    `}
`;

export const IconButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  padding: 10px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  background-color: transparent;
  transition: transform 0.2s ease;
  box-sizing: content-box;

  &:hover {
    background-color: ${({ theme }) => theme.colors.gray[200]};
  }
`;
