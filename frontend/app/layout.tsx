import type { Metadata, Viewport } from "next";

import "./globals.css";

import CookieBanner from "./components/CookieBanner";
import JsonLd from "./components/JsonLd";
import MobileHorizontalLock from "./components/MobileScrollFix";
import SiteFooter from "./components/SiteFooter";
import SiteHeader from "./components/SiteHeader";
import YandexMetrika from "./components/YandexMetrika";
import {
  SITE_DESCRIPTION,
  SITE_EMAIL,
  SITE_NAME,
  SITE_PHONE,
  SITE_URL,
} from "./lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Дома и бани из бруса под ключ — Брусодел",
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

type SiteReview = {
  id: number;
  author_name: string;
  city: string;
  text: string;
  rating: number;
  created_at?: string;
};

async function getReviews(): Promise<SiteReview[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  try {
    const response = await fetch(`${apiUrl}/reviews/`, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    return response.json();
  } catch {
    // Корневой layout оборачивает весь сайт — сбой запроса отзывов не
    // должен ронять вообще все страницы, лучше просто остаться без
    // AggregateRating в разметке для этого запроса.
    return [];
  }
}

function extractReviewDate(review: SiteReview): string | undefined {
  // Отзывы, перенесённые со старого сайта, хранят настоящую дату отзыва в
  // конце поля city через " · " (например: "Московская область, Раменское
  // · 30.10.2019") — это и есть реальная дата, в отличие от created_at
  // (момент переноса записи в текущую базу при миграции сайта).
  const match = review.city.match(/(\d{2})\.(\d{2})\.(\d{4})\s*$/);
  if (match) {
    const [, day, month, year] = match;
    return `${year}-${month}-${day}`;
  }
  return review.created_at?.slice(0, 10);
}

function buildSiteJsonLd(reviews: SiteReview[]) {
  const organizationId = `${SITE_URL}/#organization`;

  const ratingValue =
    reviews.length > 0
      ? reviews.reduce((sum, review) => sum + review.rating, 0) /
        reviews.length
      : null;

  const graph: Record<string, unknown>[] = [
    {
      "@type": "Organization",
      "@id": organizationId,
      name: 'ООО "СтройДача"',
      alternateName: "Брусодел",
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
      taxID: "4400020680",
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
      ...(ratingValue !== null
        ? {
            aggregateRating: {
              "@type": "AggregateRating",
              ratingValue: ratingValue.toFixed(1),
              reviewCount: reviews.length,
              bestRating: "5",
              worstRating: "1",
            },
          }
        : {}),
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
        "@id": organizationId,
      },
    },
  ];

  // AggregateRating без подтверждающих его отзывов — ровно то, из-за чего
  // поисковики и валидаторы структурированных данных не доверяют
  // самостоятельно опубликованному рейтингу. Публикуем реальные отзывы из
  // Django Admin (/otzyvy), а не только агрегат.
  for (const review of reviews) {
    graph.push({
      "@type": "Review",
      itemReviewed: { "@id": organizationId },
      author: {
        "@type": "Person",
        name: review.author_name,
      },
      reviewBody: review.text,
      reviewRating: {
        "@type": "Rating",
        ratingValue: review.rating,
        bestRating: "5",
        worstRating: "1",
      },
      datePublished: extractReviewDate(review),
    });
  }

  return {
    "@context": "https://schema.org",
    "@graph": graph,
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const reviews = await getReviews();
  const siteJsonLd = buildSiteJsonLd(reviews);

  return (
    <html lang="ru">
      <body>
        <JsonLd data={siteJsonLd} />
        <MobileHorizontalLock />
        <SiteHeader />

        {children}

        <SiteFooter />
        <CookieBanner />
        <YandexMetrika />
      </body>
    </html>
  );
}
