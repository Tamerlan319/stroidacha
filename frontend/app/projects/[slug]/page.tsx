import type { Metadata } from "next";
import { notFound } from "next/navigation";

import JsonLd from "../../components/JsonLd";
import LeadForm from "../../components/LeadForm";
import ImageLightbox from "../../components/ImageLightbox"

type ProjectCategory = {
  id: number;
  title: string;
  slug: string;
};

type PriceOption = {
  id: number;
  group_title: string;
  title: string;
  price: string | number | null;
  note: string;
};

type Addon = {
  id: number;
  group_title: string;
  title: string;
  price: string | number | null;
  description: string;
};

type PackageItem = {
  id: number;
  title: string;
  value: string;
};

type PackageSection = {
  id: number;
  title: string;
  items: PackageItem[];
};

type ProjectPackage = {
  id: number;
  title: string;
  price_from: string | number | null;
  description: string;
  sections: PackageSection[];
};

type ProjectImage = {
  id: number;
  image: string;
  image_type: string;
  caption: string;
  alt_text: string;
  sort_order: number;
};

type ProjectPlan = {
  id: number;
  title: string;
  image: string;
  floor: number | null;
  alt_text: string;
  sort_order: number;
};

type Project = {
  id: number;
  external_id: string | null;
  title: string;
  slug: string;
  category: ProjectCategory;
  area: string | number | null;
  floor_label: string;
  size_text: string;
  price_from: string | number | null;
  short_description: string;
  description: string;
  main_image: string | null;
  seo_title: string;
  seo_description: string;
  images: ProjectImage[];
  plans: ProjectPlan[];
  price_options: PriceOption[];
  addons: Addon[];
  packages: ProjectPackage[];
};

type PageProps = {
  params: Promise<{
    slug: string;
  }>;
};

async function getProject(slug: string): Promise<Project | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/projects/${slug}/`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Не удалось загрузить проект");
  }

  return response.json();
}

function getSiteUrl() {
  return (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(
    /\/$/,
    ""
  );
}

function getCategoryPageSlug(categorySlug: string) {
  const map: Record<string, string> = {
    houses: "doma-iz-brusa",
    baths: "bani-iz-brusa",
    garages: "garazhi-pod-klyuch",
  };

  return map[categorySlug] || categorySlug;
}

function normalizePrice(price: string | number | null) {
  if (!price) {
    return null;
  }

  const numericPrice = Number(price);

  if (Number.isNaN(numericPrice)) {
    return null;
  }

  return numericPrice;
}

function formatPrice(price: string | number | null) {
  const numericPrice = normalizePrice(price);

  if (!numericPrice) {
    return "по запросу";
  }

  return `${numericPrice.toLocaleString("ru-RU")} ₽`;
}

function getProjectDescription(project: Project) {
  return (
    project.seo_description ||
    project.short_description ||
    project.description ||
    `Проект ${project.title} с возможностью расчёта стоимости и комплектации.`
  );
}

function getProjectImages(project: Project) {
  const images = [
    project.main_image,
    ...(project.images || []).map((image) => image.image),
  ].filter(Boolean) as string[];

  return Array.from(new Set(images));
}

function groupByTitle<T extends { group_title: string }>(items: T[]) {
  return items.reduce<Record<string, T[]>>((acc, item) => {
    const group = item.group_title || "Прочее";

    if (!acc[group]) {
      acc[group] = [];
    }

    acc[group].push(item);

    return acc;
  }, {});
}

function buildProjectJsonLd(project: Project): Record<string, unknown> {
  const siteUrl = getSiteUrl();
  const pageUrl = `${siteUrl}/projects/${project.slug}`;
  const categoryPageUrl = `${siteUrl}/${getCategoryPageSlug(
    project.category.slug
  )}`;

  const description = getProjectDescription(project);
  const images = getProjectImages(project);
  const price = normalizePrice(project.price_from);

  const product: Record<string, unknown> = {
    "@type": "Product",
    "@id": `${pageUrl}#product`,
    name: project.title,
    description,
    sku: project.external_id || project.slug,
    category: project.category.title,
    image: images,
    brand: {
      "@type": "Brand",
      name: "СтройДача",
    },
  };

  if (price) {
    product.offers = {
      "@type": "Offer",
      url: pageUrl,
      priceCurrency: "RUB",
      price,
      availability: "https://schema.org/InStock",
    };
  }

  const graph: Record<string, unknown>[] = [
    {
      "@type": "WebPage",
      "@id": `${pageUrl}#webpage`,
      url: pageUrl,
      name: project.seo_title || project.title,
      description,
      inLanguage: "ru-RU",
      isPartOf: {
        "@type": "WebSite",
        "@id": `${siteUrl}#website`,
        url: siteUrl,
        name: "СтройДача",
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
          item: siteUrl,
        },
        {
          "@type": "ListItem",
          position: 2,
          name: project.category.title,
          item: categoryPageUrl,
        },
        {
          "@type": "ListItem",
          position: 3,
          name: project.title,
          item: pageUrl,
        },
      ],
    },
    product,
  ];

  if (project.main_image) {
    graph.push({
      "@type": "ImageObject",
      "@id": `${pageUrl}#primaryimage`,
      url: project.main_image,
      contentUrl: project.main_image,
      caption: project.title,
    });
  }

  return {
    "@context": "https://schema.org",
    "@graph": graph,
  };
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const project = await getProject(slug);

  if (!project) {
    return {};
  }

  const siteUrl = getSiteUrl();
  const pageUrl = `${siteUrl}/projects/${project.slug}`;
  const description = getProjectDescription(project);

  return {
    title: project.seo_title || project.title,
    description,
    alternates: {
      canonical: pageUrl,
    },
    openGraph: {
      title: project.seo_title || project.title,
      description,
      url: pageUrl,
      type: "website",
      locale: "ru_RU",
      siteName: "СтройДача",
      images: project.main_image
        ? [
            {
              url: project.main_image,
              alt: project.title,
            },
          ]
        : [],
    },
  };
}

export default async function ProjectPage({ params }: PageProps) {
  const { slug } = await params;
  const project = await getProject(slug);

  if (!project) {
    notFound();
  }

  const jsonLd = buildProjectJsonLd(project);
  const priceGroups = groupByTitle(project.price_options || []);
  const addonGroups = groupByTitle(project.addons || []);

  const galleryImages = [
  ...(project.main_image
    ? [
        {
          id: "main",
          src: project.main_image,
          alt: project.title,
          caption: "Главное изображение",
        },
      ]
    : []),
  ...(project.images || []).map((image) => ({
    id: image.id,
    src: image.image,
    alt: image.alt_text || image.caption || project.title,
    caption: image.caption,
  })),
];

  return (
    <main>
      <JsonLd data={jsonLd} />

      <section
        className="projectHero projectHeroCover"
        style={
          project.main_image
            ? { backgroundImage: `linear-gradient(90deg, rgba(16, 24, 18, 0.88), rgba(16, 24, 18, 0.48)), url(${project.main_image})` }
            : undefined
        }
      >
        <div className="container projectHeroGrid">
          <div className="projectHeroContent">
            <p className="heroKicker">{project.category.title}</p>
            <h1>{project.title}</h1>

            <p className="heroText">
              {project.short_description ||
                "Подробная карточка проекта с характеристиками, ценами и комплектацией."}
            </p>

            <div className="projectMeta">
              {project.area && <span>{project.area} м²</span>}
              {project.size_text && <span>{project.size_text}</span>}
              {project.floor_label && <span>{project.floor_label}</span>}
            </div>

            <div className="heroActions">
              <a href="#prices" className="buttonPrimary">
                Смотреть цены
              </a>
              <a href="#lead-form" className="buttonSecondary">
                Заказать проект
              </a>
            </div>
          </div>

          <aside className="projectQuoteCard">
            <strong>Получите точный расчёт</strong>
            <p>Проверим проект, комплектацию, фундамент, кровлю и доставку.</p>
            <ul>
              <li>учтём размер и планировку</li>
              <li>подберём материал</li>
              <li>рассчитаем доставку</li>
            </ul>
            <a href="#lead-form" className="buttonPrimary">
              Рассчитать проект
            </a>
          </aside>
        </div>
      </section>

      {galleryImages.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Галерея</p>
            <h2>Изображения проекта</h2>
            <p>Нажмите на изображение, чтобы открыть его в полноэкранном просмотре.</p>
          </div>

          <ImageLightbox images={galleryImages} />
        </section>
      )}

      {project.plans?.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Планировки</p>
            <h2>Планы этажей</h2>
            <p>Планировочные решения проекта. При необходимости их можно изменить.</p>
          </div>

          <div className="planGrid">
            {project.plans.map((plan) => (
              <figure className="planCard" key={plan.id}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={plan.image}
                  alt={plan.alt_text || plan.title || project.title}
                />

                <figcaption>
                  <strong>{plan.title || `План ${plan.floor || ""}`}</strong>
                  {plan.floor && <span>{plan.floor} этаж</span>}
                </figcaption>
              </figure>
            ))}
          </div>
        </section>
      )}

      {Object.keys(priceGroups).length > 0 && (
        <section className="container section" id="prices">
          <div className="sectionHeader">
            <p className="eyebrow">Стоимость</p>
            <h2>Цены по материалам</h2>
          </div>

          <div className="priceGroupGrid">
            {Object.entries(priceGroups).map(([groupTitle, items]) => (
              <div className="infoCard" key={groupTitle}>
                <h3>{groupTitle}</h3>

                <div className="priceRows">
                  {items.map((item) => (
                    <div className="priceRow" key={item.id}>
                      <span>{item.title}</span>
                      <strong>{formatPrice(item.price)}</strong>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {project.packages?.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Комплектация</p>
            <h2>Базовая комплектация</h2>
          </div>

          <div className="packageList">
            {project.packages.map((projectPackage) => (
              <div className="infoCard" key={projectPackage.id}>
                <h3>{projectPackage.title}</h3>

                {projectPackage.description && (
                  <p>{projectPackage.description}</p>
                )}

                {projectPackage.sections.map((section) => (
                  <div className="packageSection" key={section.id}>
                    <h4>{section.title}</h4>

                    <div className="packageRows">
                      {section.items.map((item) => (
                        <div className="packageRow" key={item.id}>
                          <strong>{item.title}</strong>
                          <span>{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </section>
      )}

      {Object.keys(addonGroups).length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Дополнительно</p>
            <h2>Фундамент, кровля и опции</h2>
          </div>

          <div className="priceGroupGrid">
            {Object.entries(addonGroups).map(([groupTitle, items]) => (
              <div className="infoCard" key={groupTitle}>
                <h3>{groupTitle}</h3>

                <div className="priceRows">
                  {items.map((item) => (
                    <div className="priceRow" key={item.id}>
                      <span>{item.title}</span>
                      <strong>{formatPrice(item.price)}</strong>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {project.description && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Описание</p>
            <h2>О проекте</h2>
            <p>{project.description}</p>
          </div>
        </section>
      )}

      <section className="container section" id="lead-form">
        <LeadForm
          title="Заказать этот проект"
          source="project_order"
          projectSlug={project.slug}
        />
      </section>
    </main>
  );
}