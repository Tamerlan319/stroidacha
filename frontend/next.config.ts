import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  allowedDevOrigins: [
    "192.168.1.67",
    "192.168.1.67:3000",
  ],

  devIndicators: false,

  images: {
    // Медиафайлы (фото проектов, портфолио, SEO-страниц) отдаёт Django и
    // приходят в API уже абсолютными URL — next/image требует явно
    // перечислить их хосты. Прод отдаёт всё с основного домена через Caddy;
    // остальные записи покрывают локальную разработку.
    remotePatterns: [
      { protocol: "https", hostname: "brusodel.ru" },
      { protocol: "http", hostname: "127.0.0.1", port: "8000" },
      { protocol: "http", hostname: "localhost", port: "8000" },
      { protocol: "http", hostname: "192.168.1.67", port: "8000" },
    ],
  },
};

export default nextConfig;