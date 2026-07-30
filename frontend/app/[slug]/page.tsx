import type { Metadata } from "next";
import { notFound } from "next/navigation";

import LeadForm from "../components/LeadForm";
import ProjectCatalog from "../components/ProjectCatalog";

import JsonLd from "../components/JsonLd";
import { SITE_NAME, SITE_URL } from "../lib/site";

type ProjectCategory = {
  id: number;
  title: string;
  slug: string;
};

type Project = {
  id: number;
  title: string;
  slug: string;
  category: ProjectCategory;
  area: string | null;
  floor_label: string;
  size_text: string;
  price_from: number | null;
  short_description: string;
  main_image: string | null;
};

type LandingPageFAQ = {
  id: number;
  question: string;
  answer: string;
};

type LandingPage = {
  id: number;
  title: string;
  slug: string;
  page_type: string;
  h1: string;
  intro_text: string;
  main_text: string;
  category: ProjectCategory | null;
  related_projects: Project[];
  faqs: LandingPageFAQ[];
  seo_title: string;
  seo_description: string;
};

type PageProps = {
  params: Promise<{
    slug: string;
  }>;
};

async function getLandingPage(slug: string): Promise<LandingPage | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/landing-pages/${slug}/`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Не удалось загрузить SEO-страницу");
  }

  return response.json();
}

function buildLandingPageJsonLd(page: LandingPage) {
  const pageUrl = `${SITE_URL}/${page.slug}`;

  const graph: Record<string, unknown>[] = [
    {
      "@type": page.category ? "CollectionPage" : "WebPage",
      "@id": `${pageUrl}#webpage`,
      url: pageUrl,
      name: page.seo_title || page.h1,
      description: page.seo_description || page.intro_text,
      inLanguage: "ru-RU",
      isPartOf: {
        "@type": "WebSite",
        "@id": `${SITE_URL}/#website`,
        url: SITE_URL,
        name: SITE_NAME,
      },
    },
    {
      "@type": "BreadcrumbList",
      "@id": `${pageUrl}#breadcrumbs`,
      itemListElement: [
        {
          "@type": "ListItem",
          position: 1,
          name: "Главная",
          item: SITE_URL,
        },
        {
          "@type": "ListItem",
          position: 2,
          name: page.h1,
          item: pageUrl,
        },
      ],
    },
  ];

  if (page.faqs.length > 0) {
    graph.push({
      "@type": "FAQPage",
      "@id": `${pageUrl}#faq`,
      mainEntity: page.faqs.map((faq) => ({
        "@type": "Question",
        name: faq.question,
        acceptedAnswer: {
          "@type": "Answer",
          text: faq.answer,
        },
      })),
    });
  }

  return {
    "@context": "https://schema.org",
    "@graph": graph,
  };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = await getLandingPage(slug);

  if (!page) {
    return {};
  }

  const pageUrl = `${SITE_URL}/${page.slug}`;
  const title = page.seo_title || `${page.h1} | ${SITE_NAME}`;
  const description = page.seo_description || page.intro_text;

  return {
    title: {
      absolute: title,
    },
    description,
    alternates: {
      canonical: pageUrl,
    },
    openGraph: {
      title,
      description,
      url: pageUrl,
      type: "website",
      locale: "ru_RU",
      siteName: SITE_NAME,
      images: [
        {
          url: "/images/banners/home-hero.jpg",
          alt: page.h1,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: ["/images/banners/home-hero.jpg"],
    },
  };
}

export default async function LandingPageRoute({ params }: PageProps) {
  const { slug } = await params;
  const page = await getLandingPage(slug);

  if (!page) {
    notFound();
  }

  const jsonLd = buildLandingPageJsonLd(page);

  return (
    <main>
      <JsonLd data={jsonLd} />
      <section className="landingHero">
        <div className="container landingHeroInner">
          <div>
            <p className="heroKicker">
              {page.category?.title || "Строительство из дерева"}
            </p>

            <h1>{page.h1}</h1>

            {page.intro_text && <p className="heroText">{page.intro_text}</p>}

            <div className="heroActions">
              {page.category && (
                <a href="#projects" className="buttonPrimary">
                  Смотреть проекты
                </a>
              )}
              <a href="#lead-form" className="buttonSecondary">
                Получить расчёт
              </a>
            </div>
          </div>

          <div className="landingHeroPanel">
            <strong>Бесплатный расчёт</strong>
            <p>Подберём проект, комплектацию, фундамент и доставку.</p>
            <a href="#lead-form">Оставить заявку →</a>
          </div>
        </div>
      </section>

      {page.category && (
        <ProjectCatalog
          initialCategory={page.category.slug}
          showCategoryFilter={false}
          showFilters={true}
          eyebrow="Каталог"
          title={`Проекты: ${page.h1}`}
          description="Выберите подходящий проект и уточните параметры: площадь, тип строительства и ориентировочную стоимость."
        />
      )}

      {page.main_text && (
        <section className="container section">
          <div className="textContent">
            <p className="eyebrow">Подробнее</p>
            <h2>{page.h1}</h2>
            <div className="textBlock">{page.main_text}</div>
          </div>
        </section>
      )}

      {page.faqs.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">FAQ</p>
            <h2>Частые вопросы</h2>
          </div>

          <div className="faqList">
            {page.faqs.map((faq) => (
              <details className="faqItem" key={faq.id}>
                <summary>{faq.question}</summary>
                <p>{faq.answer}</p>
              </details>
            ))}
          </div>
        </section>
      )}

      <section className="container section" id="lead-form">
        <LeadForm
          title="Получить расчёт"
          source="contact_form"
          projectSlug=""
        />
      </section>
    </main>
  );
}
