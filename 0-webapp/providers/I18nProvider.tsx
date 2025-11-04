"use client";
import React, { useEffect } from "react";
import i18next, { i18n } from "i18next";
import { I18nextProvider } from "react-i18next";
import HttpBackend from "i18next-http-backend";

let instance: i18n | null = null;

export function getInstance() {
  if (instance) return instance;
  instance = i18next.createInstance();
  instance
    .use(HttpBackend)
    .init({
      lng: "nl",
      fallbackLng: "nl",
      supportedLngs: ["nl", "en"],
      defaultNS: "common",
      ns: ["common"],
      interpolation: { escapeValue: false },
      backend: {
        loadPath: "/locales/{{lng}}/{{ns}}.json",
      },
    })
  .catch((e: unknown) => console.error("i18next init error", e));
  return instance;
}

interface I18nProviderProps {
  children: React.ReactNode;
  locale?: string;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({ children, locale }) => {
  const i18n = getInstance();
  // Detect locale from <html data-app-locale> if not provided, default to 'nl'
  const resolvedLocale =
    locale || (typeof document !== "undefined" ? document.documentElement.dataset.appLocale : "nl") || "nl";

  useEffect(() => {
    if (i18n.language !== resolvedLocale) {
      i18n.changeLanguage(resolvedLocale).catch(console.error);
    }
  }, [resolvedLocale, i18n]);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
};
