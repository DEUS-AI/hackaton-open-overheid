/** @type {import('next').NextConfig} */
const nextConfig = {
  compiler: {
    styledComponents: true,
  },
  i18n: {
    locales: ["nl", "en"],
    defaultLocale: "nl",
    // Disable automatic locale detection so visiting '/' does not get
    // rewritten to '/en' (or another locale) before our root page redirect runs.
    // This allows app/page.tsx to perform the intended redirect to '/home'.
    localeDetection: false,
  },
  webpack(config) {
    config.module.rules.push({
      test: /\.svg$/,
      use: ["@svgr/webpack"],
    });
    return config;
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  output: "standalone",
};

export default nextConfig;
