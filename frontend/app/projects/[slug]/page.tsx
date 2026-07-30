import type { Metadata } from "next";
import { notFound } from "next/navigation";

import JsonLd from "../../components/JsonLd";
import LeadForm from "../../components/LeadForm";
import ImageLightbox from "../../components/ImageLightbox";
import { SITE_NAME, SITE_URL } from "../../lib/site";

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
  content_sections: ProjectContentSection[];
  illustrated_options: ProjectIllustratedOption[];
};

type PageProps = {
  params: Promise<{
    slug: string;
  }>;
};

type ProjectContentSection = {
  id: number;
  title: string;
  body: string;
  sort_order: number;
};

type ProjectIllustratedOption = {
  id: number;
  group_title: string;
  title: string;
  price: string | number | null;
  image: string | null;
  description: string;
  sort_order: number;
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
  const pageUrl = `${SITE_URL}/projects/${project.slug}`;
  const categoryPageUrl = `${SITE_URL}/${getCategoryPageSlug(
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
      name: SITE_NAME,
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

  const pageUrl = `${SITE_URL}/projects/${project.slug}`;
  const description = getProjectDescription(project);
  const title = project.seo_title || `${project.title} | ${SITE_NAME}`;
  const images = project.main_image
    ? [{ url: project.main_image, alt: project.title }]
    : [{ url: "/images/banners/home-hero.jpg", alt: project.title }];

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
      images,
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: images.map((image) => image.url),
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

  const galleryImages = (project.images || []).map((image) => ({
    id: image.id,
    src: image.image,
    alt: image.alt_text || image.caption || project.title,
    caption: image.caption,
  }));

  const planImages = (project.plans || []).map((plan) => ({
  id: plan.id,
  src: plan.image,
  alt: plan.alt_text || plan.title || project.title,
  caption: plan.title || `План ${plan.floor || ""}`,
  }));

  const contentSections = project.content_sections || [];
  const illustratedOptionGroups = groupByTitle(project.illustrated_options || []);

  return (
    <main className="projectPage">
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
          </div>

          <ImageLightbox images={galleryImages} previewLimit={5} />
        </section>
      )}

      {planImages.length > 0 && (
        <section className="container section projectPlansSection">
          <div className="sectionHeader sectionHeaderCompact">
            <p className="eyebrow">Планировки</p>
            <h2>Планы этажей</h2>
            <p>
              Нажмите на планировку, чтобы открыть её крупно и рассмотреть детали.
            </p>
          </div>

          <ImageLightbox
            images={planImages}
            previewLimit={4}
            className="projectGalleryPlans"
          />
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

      {Object.keys(illustratedOptionGroups).length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Материалы и решения</p>
            <h2>Дополнительные варианты для проекта</h2>
            <p>
              Фундамент, кровля и другие решения, которые можно добавить или заменить
              при расчёте проекта.
            </p>
          </div>

          <div className="illustratedOptionGroups">
            {Object.entries(illustratedOptionGroups).map(([groupTitle, items]) => (
              <div className="illustratedOptionGroup" key={groupTitle}>
                <h3>{groupTitle}</h3>

                <div className="illustratedOptionGrid">
                  {items.map((item) => (
                    <article className="illustratedOptionCard" key={item.id}>
                      <div className="illustratedOptionImage">
                        {item.image ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={item.image} alt={item.title} />
                        ) : (
                          <div className="imagePlaceholder">Изображение</div>
                        )}
                      </div>

                      <div className="illustratedOptionBody">
                        <h4>{item.title}</h4>

                        {item.description && <p>{item.description}</p>}

                        <strong>{formatPrice(item.price)}</strong>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {contentSections.length > 0 ? (
        <section className="container section">
          <div className="sectionHeader sectionHeaderCenter">
            <p className="eyebrow">Описание</p>
            <h2>Подробно о проекте</h2>
          </div>

          <div className="projectTextSections">
            {contentSections.map((section) => (
              <article className="projectTextSection" key={section.id}>
                <h3>{section.title}</h3>
                <p>{section.body}</p>
              </article>
            ))}
          </div>
        </section>
      ) : (
        project.description && (
          <section className="container section">
            <div className="sectionHeader sectionHeaderCenter">
              <p className="eyebrow">Описание</p>
              <h2>О проекте</h2>
              <p>{project.description}</p>
            </div>
          </section>
        )
      )}
    </main>
  );
}
