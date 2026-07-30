import type { MetadataRoute } from "next";

import { SITE_DESCRIPTION, SITE_NAME } from "./lib/site";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: `${SITE_NAME} — дома и бани из бруса`,
    short_name: SITE_NAME,
    description: SITE_DESCRIPTION,
    start_url: "/",
    display: "standalone",
    background_color: "#f4f1ea",
    theme_color: "#1f3325",
    lang: "ru",
    icons: [
      {
        src: "/brand/brusoteka-logo-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/brand/brusoteka-logo-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
