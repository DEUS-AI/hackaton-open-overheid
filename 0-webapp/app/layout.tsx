import "@livekit/components-styles";
import { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "../providers/ThemeProvider";
import { I18nProvider } from "../providers/I18nProvider";
import { Notifications } from "@mantine/notifications";
import NavBar from "../components/NavBar";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";

export const metadata: Metadata = {
  title: "Voice Assistant",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
  <html lang="nl">
    <head>
      <link rel="icon" href="/favicon.ico"/>
    </head>
    <body>
      <I18nProvider>
        <ThemeProvider>
          <Notifications position="top-right" />
          <div>
            <NavBar />
            <main>{children}</main>
          </div>
        </ThemeProvider>
      </I18nProvider>
    </body>
  </html>
  );
}
