import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  allowedDevOrigins: [
    "192.168.1.67",
    "192.168.1.67:3000",
  ],

  devIndicators: false,
};

export default nextConfig;