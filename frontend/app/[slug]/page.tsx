import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import Breadcrumbs, { BreadcrumbItem } from "../components/Breadcrumbs";
import LeadForm from "../components/LeadForm";
import ProjectCatalog from "../components/ProjectCatalog";
import RichText from "../components/RichText";

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

type LandingPageImage = {
  id: number;
  image: string | null;
  alt_text: string;
  caption: string;
  sort_order: number;
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
  images: LandingPageImage[];
  filter_width: string | number | null;
  filter_length: string | number | null;
  seo_title: string;
  seo_description: string;
};

type SiblingPage = {
  slug: string;
  page_type: string;
  h1: string;
};

type PageProps = {
  params: Promise<{
    slug: string;
  }>;
};

const landingCategoryBySlug: Record<string, ProjectCategory> = {
  "doma-iz-brusa": { id: 0, slug: "houses", title: "Дома" },
  "bani-iz-brusa": { id: 0, slug: "baths", title: "Бани" },
};

// Подписи для карточек в блоке "Смотрите также" — держим в соответствии с
// seo.models.LandingPage.PageType на бэкенде.
const PAGE_TYPE_LABELS: Record<string, string> = {
  service: "Каталог",
  size: "Размер",
  material: "Материал",
  region: "Регион",
  delivery: "Доставка",
  production: "Производство",
  company: "О компании",
  guide: "Справочник",
  custom: "Страница",
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

// Соседние SEO-страницы того же раздела каталога (хаб, размеры, регион) —
// блок "Смотрите также" ниже. Не показываем на страницах без category
// (справочные статьи вроде "ипотека" или "доставка" не входят ни в один
// каталожный раздел, и это ожидаемо).
async function getSiblingPages(
  categorySlug: string,
  currentSlug: string,
): Promise<SiblingPage[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  try {
    const response = await fetch(
      `${apiUrl}/landing-pages/?category=${encodeURIComponent(categorySlug)}`,
      { cache: "no-store" },
    );

    if (!response.ok) {
      return [];
    }

    const pages: SiblingPage[] = await response.json();
    // Каталог размерных страниц может вырасти до пары десятков — ограничиваем
    // блок, чтобы он оставался ссылкой "по теме", а не второй картой сайта.
    // Полный список всё равно доступен через sitemap.xml.
    return pages.filter((page) => page.slug !== currentSlug).slice(0, 12);
  } catch {
    return [];
  }
}

function buildBreadcrumbItems(page: LandingPage): BreadcrumbItem[] {
  const items: BreadcrumbItem[] = [{ name: "Главная", href: "/" }];

  if (page.category) {
    // Хаб-страница ("Дома из бруса") сама себе не родитель — крошку между
    // "Главная" и её h1 вставляем только для дочерних страниц раздела
    // (размерных, региональных и т.д.), у которых slug хаба другой.
    const hubSlug = Object.entries(landingCategoryBySlug).find(
      ([, category]) => category.slug === page.category!.slug,
    )?.[0];

    if (hubSlug && hubSlug !== page.slug) {
      items.push({ name: page.category.title, href: `/${hubSlug}` });
    }
  }

  items.push({ name: page.h1 });
  return items;
}

function absoluteBreadcrumbUrl(href: string | undefined, fallback: string): string {
  if (!href) return fallback;
  return href === "/" ? SITE_URL : `${SITE_URL}${href}`;
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
      itemListElement: buildBreadcrumbItems(page).map((item, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: item.name,
        item: absoluteBreadcrumbUrl(item.href, pageUrl),
      })),
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

  // Для главных страниц каталогов URL — источник истины. Даже если редактор
  // случайно привязал страницу бань к категории домов, посетитель увидит бани.
  const catalogCategory = landingCategoryBySlug[slug] || page.category;
  const jsonLd = buildLandingPageJsonLd(page);

  const siblingPages = catalogCategory
    ? await getSiblingPages(catalogCategory.slug, page.slug)
    : [];

  // Размерные страницы (например, "Дома из бруса 6х6") задают точный
  // footprint через filter_width/filter_length в админке. Если поля не
  // заполнены, каталог показывает всю категорию — это ожидаемо для
  // страниц-хабов вроде "Дома из бруса".
  const filterWidth = page.filter_width ? Number(page.filter_width) : undefined;
  const filterLength = page.filter_length ? Number(page.filter_length) : undefined;
  const catalogDescription =
    filterWidth && filterLength
      ? `Показаны проекты размером ${filterWidth}×${filterLength} м. Уточните дополнительные параметры: тип строительства и ориентировочную стоимость.`
      : "Выберите подходящий проект и уточните параметры: площадь, тип строительства и ориентировочную стоимость.";

  return (
    <main>
      <JsonLd data={jsonLd} />
      <Breadcrumbs items={buildBreadcrumbItems(page)} />
      <section className="landingHero">
        <div className="container landingHeroInner">
          <div>
            <p className="heroKicker">
              {catalogCategory?.title || "Строительство из дерева"}
            </p>

            <h1>{page.h1}</h1>

            {page.intro_text && <p className="heroText">{page.intro_text}</p>}

            <div className="heroActions">
              {catalogCategory && (
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

      {catalogCategory && (
        <ProjectCatalog
          initialCategory={catalogCategory.slug}
          showCategoryFilter={false}
          showFilters={true}
          filterWidth={filterWidth}
          filterLength={filterLength}
          eyebrow="Каталог"
          title={`Проекты: ${page.h1}`}
          description={catalogDescription}
        />
      )}

      {page.main_text && (
        <section className="container section">
          <div className="textContent">
            <p className="eyebrow">Подробнее</p>
            <h2>{page.h1}</h2>
            <RichText value={page.main_text} />
          </div>
        </section>
      )}

      {siblingPages.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Смотрите также</p>
            <h2>Похожие страницы каталога</h2>
          </div>

          <div className="seoLinkGrid">
            {siblingPages.map((sibling) => (
              <Link
                className="seoLinkCard"
                href={`/${sibling.slug}`}
                key={sibling.slug}
              >
                <span>{PAGE_TYPE_LABELS[sibling.page_type] || "Страница"}</span>
                <strong>{sibling.h1}</strong>
              </Link>
            ))}
          </div>
        </section>
      )}

      {(page.images || []).length > 0 && (
        <section className="container section landingMediaSection">
          <div className="sectionHeader">
            <p className="eyebrow">
              {page.slug === "vypiska-iz-egryul" ? "Документы" : "Фотографии"}
            </p>
            <h2>
              {page.slug === "vypiska-iz-egryul"
                ? "Выписка из ЕГРЮЛ"
                : "Материалы страницы"}
            </h2>
          </div>

          <div
            className={`landingMediaGrid ${
              page.slug === "vypiska-iz-egryul"
                ? "landingMediaDocuments"
                : ""
            }`}
          >
            {(page.images || [])
              .filter((item) => item.image)
              .map((item) => (
                <a
                  href={item.image || "#"}
                  key={item.id}
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    alt={item.alt_text || item.caption || page.h1}
                    src={item.image || ""}
                  />
                  {item.caption && <span>{item.caption}</span>}
                </a>
              ))}
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
