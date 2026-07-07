import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "192.168.1.67",
    "192.168.1.67:3000",
  ],
};

export default nextConfig;