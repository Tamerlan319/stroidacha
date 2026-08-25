import type { MetadataRoute } from "next";

import { SITE_URL } from "./lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
        "/api/",
        "/admin/",
        // Вложения заявок теперь хранятся вне /media/ (см. leads/storage.py)
        // и отдаются только через авторизованный view — здесь на всякий
        // случай, второй защитный слой, а не единственная защита.
        "/media/leads/",
      ],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
