import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow Playwright to run a second `next dev` against a separate dist dir
  // (see playwright.config.ts: the flag-off webServer sets NEXT_DIST_DIR).
  ...(process.env.NEXT_DIST_DIR ? { distDir: process.env.NEXT_DIST_DIR } : {}),
  async redirects() {
    return [
      {
        source: "/forecasting/report/:id",
        destination: "/report/:id",
        permanent: true,
      },
      {
        source: "/forecasting/predicting",
        destination: "/report/predicting",
        permanent: true,
      },
      {
        source: "/forecasting",
        destination: "/report",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
