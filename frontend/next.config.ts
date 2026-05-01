import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
