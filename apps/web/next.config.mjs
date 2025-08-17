import withPWAInit from "next-pwa";

const withPWA = withPWAInit({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  skipWaiting: true,
});

const nextConfig = withPWA({
  i18n: {
    locales: ["ko", "en"],
    defaultLocale: "en",
  },
});

export default nextConfig;
