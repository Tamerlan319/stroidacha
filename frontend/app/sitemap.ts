import type { MetadataRoute } from "next";

import { SITE_URL } from "./lib/site";

type Project = {
  slug: string;
};

type LandingPage = {
  slug: string;
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

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [projects, landingPages] = await Promise.all([
    getProjects(),
    getLandingPages(),
  ]);

  const staticPages: MetadataRoute.Sitemap = [
    {
      url: SITE_URL,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${SITE_URL}/calculator`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${SITE_URL}/portfolio`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/kontakty`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${SITE_URL}/spravochnik`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/otzyvy`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${SITE_URL}/faq`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
  ];

  const projectPages: MetadataRoute.Sitemap = projects.map((project) => ({
    url: `${SITE_URL}/projects/${project.slug}`,
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  const seoPages: MetadataRoute.Sitemap = landingPages.map((page) => ({
    url: `${SITE_URL}/${page.slug}`,
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: 0.9,
  }));

  return [...staticPages, ...seoPages, ...projectPages];
}
