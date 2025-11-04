"use client";

import { ThemeProvider as StyledThemeProvider } from "styled-components";
import { theme } from "../styles/theme";
import { MantineProvider, createTheme, MantineColorsTuple } from "@mantine/core";
import React from "react";

// Professional government color palettes
const govBlue: MantineColorsTuple = [
  "#e8f0f7",
  "#d1e1f0",
  "#a3c3e1",
  "#72a4d1",
  "#4b88c3",
  "#3073b8",
  "#153a66", // Primary government blue
  "#1e4d7a",
  "#173f63",
  "#10324f",
];

const govGreen: MantineColorsTuple = [
  "#e8f5e8",
  "#d1ebd1",
  "#a3d6a3",
  "#74c174",
  "#4cae4c",
  "#359d35",
  "#1e7e1e", // Success green
  "#186818",
  "#135213",
  "#0e3c0e",
];

const govRed: MantineColorsTuple = [
  "#fde8e8",
  "#fbd1d1",
  "#f7a3a3",
  "#f37474",
  "#ef4c4c",
  "#eb3030",
  "#d42c2c", // Error red
  "#b82424",
  "#9c1d1d",
  "#801616",
];

const govAmber: MantineColorsTuple = [
  "#fef3e8",
  "#fce7d1",
  "#f9cfa3",
  "#f6b774",
  "#f3a04c",
  "#f0923a",
  "#ed8530", // Warning amber
  "#d47228",
  "#ba5f20",
  "#a04c18",
];

const govGray: MantineColorsTuple = [
  "#f8f9fa",
  "#e9ecef",
  "#dee2e6",
  "#ced4da",
  "#adb5bd",
  "#6c757d",
  "#495057", // Professional gray
  "#343a40",
  "#212529",
  "#16191c",
];

// Comprehensive Mantine theme for government application
const mantineTheme = createTheme({
  colors: {
    // Primary government blue
    govBlue,
    // Supporting colors
    govGreen,
    govRed,
    govAmber,
    govGray,
    // Keep original brand for backward compatibility
    brand: govBlue,
  },
  primaryColor: "govBlue",
  
  // Typography
  fontFamily: theme.typography.fontFamily,
  headings: {
    fontFamily: theme.typography.fontFamily,
    sizes: {
      h1: { fontSize: '2.125rem', fontWeight: '700', lineHeight: '1.2' },
      h2: { fontSize: '1.625rem', fontWeight: '600', lineHeight: '1.3' },
      h3: { fontSize: '1.375rem', fontWeight: '600', lineHeight: '1.4' },
      h4: { fontSize: '1.125rem', fontWeight: '500', lineHeight: '1.45' },
      h5: { fontSize: '1rem', fontWeight: '500', lineHeight: '1.5' },
      h6: { fontSize: '0.875rem', fontWeight: '500', lineHeight: '1.5' },
    },
  },
  
  // Spacing system
  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },

  // Border radius - more conservative for government apps
  radius: {
    xs: '0.125rem',
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
  },

  // Shadow system - subtle shadows for professional look
  shadows: {
    xs: '0 1px 3px rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)',
  },

  // Component-specific styling
  components: {
    Button: {
      defaultProps: {
        size: 'md',
      },
      styles: {
        root: {
          fontWeight: 500,
          borderRadius: '0.375rem',
        },
      },
    },
    Card: {
      defaultProps: {
        shadow: 'sm',
        radius: 'md',
      },
      styles: {
        root: {
          border: '1px solid #e9ecef',
        },
      },
    },
    Paper: {
      defaultProps: {
        shadow: 'xs',
        radius: 'md',
      },
    },
    Input: {
      styles: {
        input: {
          borderRadius: '0.375rem',
          border: '1px solid #ced4da',
          '&:focus': {
            borderColor: govBlue[6],
            boxShadow: `0 0 0 2px ${govBlue[1]}`,
            outline: `2px solid ${govBlue[6]}`,
            outlineOffset: '2px',
          },
        },
      },
    },
    Badge: {
      styles: {
        root: {
          fontWeight: 500,
        },
      },
    },
    Notification: {
      styles: {
        root: {
          borderRadius: '0.5rem',
        },
      },
    },
  },

  other: {
    appTheme: theme,
    // Additional government-specific theme values
    gov: {
      colors: {
        primary: govBlue[6],
        secondary: govGray[6],
        success: govGreen[6],
        warning: govAmber[6],
        error: govRed[6],
        info: govBlue[4],
      },
      accessibility: {
        focusRing: `2px solid ${govBlue[6]}`,
        focusRingOffset: '2px',
        highContrast: true,
      },
      // LiveKit specific styling
      livekit: {
        agentVisualizer: {
          backgroundColor: 'transparent',
        },
        audioBar: {
          width: '72px',
        },
        controlBar: {
          borderTop: 0,
          padding: 0,
          height: 'min-content',
          marginRight: '1rem',
        },
        disconnectButton: {
          height: '36px',
          backgroundColor: '#31100c',
          borderColor: '#6b221a',
          hoverBackgroundColor: '#6b221a',
          hoverColor: 'white',
        },
      },
    },
  },
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <StyledThemeProvider theme={theme}>
      <MantineProvider theme={mantineTheme} defaultColorScheme="light">
        {children}
      </MantineProvider>
    </StyledThemeProvider>
  );
}
