import type { Metadata, Viewport } from "next";
import YandexMetrika from "./components/YandexMetrika";
import "./globals.css";

import JsonLd from "./components/JsonLd";
import SiteFooter from "./components/SiteFooter";
import SiteHeader from "./components/SiteHeader";
import {
  SITE_DESCRIPTION,
  SITE_EMAIL,
  SITE_NAME,
  SITE_PHONE,
  SITE_URL,
} from "./lib/site";

import MobileHorizontalLock from "./components/MobileScrollFix";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Дома и бани из бруса под ключ — Брусотека",
    template: `%s | ${SITE_NAME}`,
  },
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  category: "Строительство",
  creator: SITE_NAME,
  publisher: SITE_NAME,
  formatDetection: {
    address: false,
    email: false,
    telephone: false,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#1f3325",
};

const siteJsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: SITE_NAME,
      alternateName: "Брусотека — дома из бруса",
      url: SITE_URL,
      logo: {
        "@type": "ImageObject",
        url: `${SITE_URL}/brand/brusoteka-logo-512.png`,
        width: 512,
        height: 512,
      },
      image: `${SITE_URL}/images/banners/home-hero.jpg`,
      description: SITE_DESCRIPTION,
      email: SITE_EMAIL,
      telephone: SITE_PHONE,
      areaServed: {
        "@type": "Country",
        name: "Россия",
      },
      contactPoint: {
        "@type": "ContactPoint",
        telephone: SITE_PHONE,
        email: SITE_EMAIL,
        contactType: "sales",
        areaServed: "RU",
        availableLanguage: ["Russian"],
      },
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: SITE_URL,
      name: SITE_NAME,
      alternateName: "Дома и бани из бруса под ключ",
      description: SITE_DESCRIPTION,
      inLanguage: "ru-RU",
      publisher: {
        "@id": `${SITE_URL}/#organization`,
      },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>
        <JsonLd data={siteJsonLd} />
        <MobileHorizontalLock />
        <SiteHeader />

        {children}

        <SiteFooter />
      </body>
      <YandexMetrika />
    </html>
  );
}
