import type { MetadataRoute } from "next";

import { SITE_URL } from "./lib/site";

type Project = {
  slug: string;
  updated_at?: string;
};

type LandingPage = {
  slug: string;
  updated_at?: string;
};

async function getProjects(): Promise<Project[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  try {
    const response = await fetch(`${apiUrl}/projects/`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return [];
    }

    return response.json();
  } catch {
    return [];
  }
}

async function getLandingPages(): Promise<LandingPage[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  try {
    const response = await fetch(`${apiUrl}/landing-pages/`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return [];
    }

    return response.json();
  } catch {
    return [];
  }
}

// Для карточек проектов и SEO-страниц бэкенд отдаёт настоящую дату
// последнего изменения (updated_at). Для статических разделов (главная,
// калькулятор и т.д.) у нас нет per-страничного трекинга правок, поэтому
// lastModified для них намеренно не проставляется — Google и Яндекс
// трактуют это поле как опциональное, и отсутствующая дата лучше, чем
// придуманная (раньше здесь стоял new Date() на каждый запрос сайтмапа,
// что делало сигнал lastmod бесполезным для всех 150+ URL сразу).
function toLastModified(value?: string): Date | undefined {
  if (!value) return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [projects, landingPages] = await Promise.all([
    getProjects(),
    getLandingPages(),
  ]);

  const staticPages: MetadataRoute.Sitemap = [
    {
      url: SITE_URL,
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${SITE_URL}/calculator`,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/portfolio`,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/kontakty`,
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${SITE_URL}/spravochnik`,
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/otzyvy`,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/faq`,
      changeFrequency: "monthly",
      priority: 0.7,
    },
  ];

  const projectPages: MetadataRoute.Sitemap = projects.map((project) => ({
    url: `${SITE_URL}/projects/${project.slug}`,
    lastModified: toLastModified(project.updated_at),
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  const seoPages: MetadataRoute.Sitemap = landingPages.map((page) => ({
    url: `${SITE_URL}/${page.slug}`,
    lastModified: toLastModified(page.updated_at),
    changeFrequency: "weekly",
    priority: 0.9,
  }));

  return [...staticPages, ...seoPages, ...projectPages];
}
