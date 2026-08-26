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
    // На проде контейнер сам себе резолвит brusodel.ru на внутренний IP
    // Caddy в docker-сети (см. docker-compose.prod.yml, network alias) —
    // без этого публичный плавающий IP не поддерживает hairpin NAT обратно
    // на себя же (см. коммит с фиксом NEXT_PUBLIC_API_URL). Из-за алиаса
    // резолвится приватный адрес, и next/image по умолчанию блокирует такую
    // оптимизацию как потенциальный SSRF. Здесь это безопасно: src всегда
    // приходит из доверенных ответов Django API, а не от пользователя, и
    // remotePatterns выше и так ограничивает хосты только нашим доменом.
    dangerouslyAllowLocalIP: true,
  },
};

export default nextConfig;