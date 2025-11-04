import { DefaultTheme } from "styled-components";

declare module "styled-components" {
  export interface DefaultTheme {
    colors: {
      primary: string;
      secondary: string;
      background: string;
      text: string;
      error: string;
      success: string;
      gray: {
        100: string;
        200: string;
        300: string;
        400: string;
        500: string;
        600: string;
        700: string;
        800: string;
        900: string;
      };
    };

    spacing: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
    breakpoints: {
      mobile: string;
      tablet: string;
      desktop: string;
    };
    typography: {
      fontFamily: string;
      fontSize: {
        small: string;
        medium: string;
        large: string;
        xlarge: string;
      };
      fontWeight: {
        regular: number;
        medium: number;
        bold: number;
      };
    };
  }
}

export const theme: DefaultTheme = {
  colors: {
    primary: "rgb(21,58,102)",
    secondary: "#5856D6",
    // background: "rgba(32, 32, 32, 1)",
    // text: "#fff",
    background: "#fff",
    text: "rgba(32,32,32)",
    error: "#FF3B30",
    success: "#34C759",
    gray: {
      100: "#F2F2F2",
      200: "#E5E5E5",
      300: "#D4D4D4",
      400: "#A3A3A3",
      500: "#737373",
      600: "#525252",
      700: "#404040",
      800: "#262626",
      900: "#171717",
    },
  },

  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
  },
  breakpoints: {
    mobile: "320px",
    tablet: "768px",
    desktop: "1024px",
  },
  typography: {
    fontFamily:
      '"Segoe UI", Roboto, sans-serif',
    fontSize: {
      small: "0.875rem",
      medium: "1rem",
      large: "1.25rem",
      xlarge: "1.5rem",
    },
    fontWeight: {
      regular: 400,
      medium: 500,
      bold: 700,
    },
  },
};
