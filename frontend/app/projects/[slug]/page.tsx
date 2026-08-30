import type { Metadata } from "next";
import Image from "next/image";
import { notFound } from "next/navigation";

import Link from "next/link";

import JsonLd from "../../components/JsonLd";
import LeadForm from "../../components/LeadForm";
import ImageLightbox from "../../components/ImageLightbox";
import ProjectGalleryWithPrices from "../../components/ProjectGalleryWithPrices";
import SiteIcon from "../../components/SiteIcon";
import { SITE_NAME, SITE_URL } from "../../lib/site";
import detailsStyles from "./ProjectDetails.module.css";

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

type SimilarProject = {
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
  main_image: string | null;
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
  promotions: ProjectPromotion[];
  work_steps: ProjectWorkStep[];
  similar_projects: SimilarProject[];
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
type ProjectPromotion = {
  id: number;
  code: string;
  title: string;
  description: string;
  image: string | null;
  button_label: string;
  sort_order: number;
};

type ProjectWorkStep = {
  id: number;
  code: string;
  title: string;
  description: string;
  icon: "blueprint" | "contract" | "truck" | "house" | "shield";
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
function formatContentHeading(title: string) {
  const normalized = title.trim().toLocaleUpperCase("ru-RU");
  const knownHeadings: Record<string, string> = {
    "ОПИСАНИЕ ПРОЕКТА": "Описание проекта",
    "ВИДЫ БРУСА ДЛЯ ДОМА, ИХ ОТЛИЧИЕ И ЗНАЧЕНИЕ": "Виды бруса и выбор материала",
    "ВАРИАНТЫ ФУНДАМЕНТОВ, КРОВЛИ И ЧТО ВХОДИТ В СТОИМОСТЬ": "Фундамент, кровля и состав стоимости",
    "ЧТО ЕЩЕ ВАЖНО ЗНАТЬ": "Что ещё важно знать",
  };
  if (knownHeadings[normalized]) return knownHeadings[normalized];
  if (title === normalized) {
    const lower = title.toLocaleLowerCase("ru-RU");
    return lower.charAt(0).toLocaleUpperCase("ru-RU") + lower.slice(1);
  }
  return title;
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
  const projectMedia = [
    ...(project.main_image
      ? [
          {
            id: "main-image",
            src: project.main_image,
            alt: project.title,
            caption: "Главное фото",
            kind: "image",
          },
        ]
      : []),
    ...(project.images || []).map((image) => ({
      id: `image-${image.id}`,
      src: image.image,
      alt: image.alt_text || image.caption || project.title,
      caption: image.caption || "Изображение проекта",
      kind: image.image_type || "image",
    })),
  ].filter(
    (item, index, allItems) =>
      allItems.findIndex((candidate) => candidate.src === item.src) === index,
  );
  const planImages = (project.plans || []).map((plan) => ({
    id: plan.id,
    src: plan.image,
    alt: plan.alt_text || plan.title || project.title,
    caption: plan.title || `План ${plan.floor || ""}`,
  }));

  const priceSections = Object.entries(priceGroups).map(([title, items]) => ({
    title,
    items: items.map((item) => ({
      id: item.id,
      title: item.title,
      price: formatPrice(item.price),
    })),
  }));

  const contentSections = project.content_sections || [];
  const illustratedOptionGroups = groupByTitle(project.illustrated_options || []);
  const promotions = project.promotions || [];
  const workSteps = project.work_steps || [];
  const similarProjects = project.similar_projects || [];
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
      {(projectMedia.length > 0 || priceSections.length > 0) && (
        <ProjectGalleryWithPrices
          images={projectMedia}
          priceGroups={priceSections}
        />
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
        <section className="projectOptionsSection">
          <div className="container section">
            <div className="sectionHeader projectSectionIntro">
              <p className="eyebrow">Конструктивные решения</p>
              <h2>Фундамент и чистовая кровля</h2>
              <p>Выберите подходящий вариант — стоимость рассчитана именно для этого проекта.</p>
            </div>
            <div className="projectOptionGroups">
              {Object.entries(illustratedOptionGroups).map(([groupTitle, items]) => (
                <div className={`projectOptionGroup ${items.length <= 2 ? "isCompact" : ""}`} key={groupTitle}>
                  <div className="projectOptionGroupHeading">
                    <span><SiteIcon name={groupTitle.includes("Фундамент") ? "foundation" : "house"} /></span>
                    <div>
                      <p>{groupTitle.includes("Фундамент") ? "Основание дома" : "Вместо временной кровли"}</p>
                      <h3>{groupTitle}</h3>
                    </div>
                  </div>
                  <div className="projectOptionGrid">
                    {items.map((item) => (
                      <article className="projectOptionCard" key={item.id}>
                        <div className="projectOptionImage">
                          {item.image ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={item.image} alt={item.title} />
                          ) : (
                            <SiteIcon name={groupTitle.includes("Фундамент") ? "foundation" : "house"} />
                          )}
                        </div>
                        <div className="projectOptionBody">
                          <h4>{item.title}</h4>
                          {item.description && !item.description.toLowerCase().includes("импортировано") && (
                            <p>{item.description}</p>
                          )}
                          <strong>{formatPrice(item.price)}</strong>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
      {similarProjects.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Похожие проекты</p>
            <h2>Другие варианты в категории «{project.category.title}»</h2>
          </div>

          <div className="projectGrid">
            {similarProjects.map((similar) => (
              <article className="projectCard" key={similar.id}>
                <Link className="projectImage" href={`/projects/${similar.slug}`}>
                  {similar.main_image ? (
                    <Image
                      src={similar.main_image}
                      alt={similar.title}
                      fill
                      sizes="(max-width: 680px) 100vw, (max-width: 1100px) 50vw, 33vw"
                      style={{ objectFit: "cover" }}
                    />
                  ) : (
                    <div className="imagePlaceholder">Фото проекта</div>
                  )}
                  <span className="projectBadge">{similar.category.title}</span>
                </Link>

                <div className="projectBody">
                  <div className="projectTop">
                    <span>{similar.size_text || "Размер уточняется"}</span>
                    {similar.area && <span>{similar.area} м²</span>}
                  </div>

                  <h3>{similar.title}</h3>

                  <p>
                    {similar.short_description ||
                      "Описание проекта скоро появится."}
                  </p>

                  <div className="projectSpecs">
                    {similar.floor_label && <span>{similar.floor_label}</span>}
                    {similar.external_id && <span>{similar.external_id}</span>}
                  </div>

                  <div className="projectFooter">
                    <strong>{formatPrice(similar.price_from)}</strong>
                    <Link href={`/projects/${similar.slug}`}>Подробнее</Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
      {contentSections.length > 0 ? (
        <section className={`container section ${detailsStyles.section}`}>
          <div className={detailsStyles.heading}>
            <div>
              <p className="eyebrow">Описание</p>
              <h2>Подробно о проекте</h2>
            </div>
            <p>
              Основные особенности проекта, конструктивные решения и важные
              детали комплектации.
            </p>
          </div>

          <div className={detailsStyles.grid}>
            {contentSections.map((section, sectionIndex) => (
              <article className={detailsStyles.card} key={section.id}>
                <div className={detailsStyles.cardTop}>
                  <span className={detailsStyles.number}>
                    {String(sectionIndex + 1).padStart(2, "0")}
                  </span>
                  <h3>{formatContentHeading(section.title)}</h3>
                </div>

                <div className={detailsStyles.text}>
                  {section.body.split(/\n{2,}/).map((paragraph, index) => (
                    <p key={`${section.id}-${index}`}>{paragraph}</p>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : (
        project.description && (
          <section className={`container section ${detailsStyles.section}`}>
            <div className={detailsStyles.heading}>
              <div>
                <p className="eyebrow">Описание</p>
                <h2>Подробно о проекте</h2>
              </div>
              <p>
                Общая информация о планировке, конструкции и назначении
                проекта.
              </p>
            </div>

            <article
              className={`${detailsStyles.card} ${detailsStyles.singleCard}`}
            >
              <div className={detailsStyles.cardTop}>
                <span className={detailsStyles.number}>01</span>
                <h3>{project.title}</h3>
              </div>
              <div className={detailsStyles.text}>
                <p>{project.description}</p>
              </div>
            </article>
          </section>
        )
      )}
      {promotions.length > 0 && (
        <section className="projectPromotions">
          <div className="container section">
            <div className="sectionHeader projectSectionIntro">
              <p className="eyebrow">Выгодные условия</p>
              <h2>Действующие акции</h2>
              <p>Актуальные предложения можно включить в расчёт проекта.</p>
            </div>
            <div className="projectPromotionGrid">
              {promotions.map((promotion) => (
                <article className="projectPromotionCard" key={promotion.id}>
                  <div className="projectPromotionImage">
                    {promotion.image ? (
                      <Image
                        src={promotion.image}
                        alt={promotion.title}
                        fill
                        sizes="(max-width: 780px) 100vw, 380px"
                        style={{ objectFit: "cover" }}
                      />
                    ) : (
                      <SiteIcon name="gift" />
                    )}
                  </div>
                  <div>
                    <h3>{promotion.title}</h3>
                    {promotion.description && <p>{promotion.description}</p>}
                    <a href="#lead-form">{promotion.button_label || "Узнать подробнее"} →</a>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      )}
      {workSteps.length > 0 && (
        <section className="container section projectWorkSection">
          <div className="sectionHeader projectSectionIntro">
            <p className="eyebrow">Понятный процесс</p>
            <h2>Этапы работы</h2>
          </div>
          <div className="projectWorkGrid">
            {workSteps.map((step, index) => (
              <article className="projectWorkCard" key={step.id}>
                <span className="projectWorkNumber">{String(index + 1).padStart(2, "0")}</span>
                <SiteIcon name={step.icon} />
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </section>
      )}
      <section className="projectLeadSection" id="lead-form">
        <div className="container section projectLeadGrid">
          <div>
            <p className="eyebrow">Расчёт проекта</p>
            <h2>Узнайте точную стоимость строительства</h2>
            <p>Менеджер уточнит комплектацию, фундамент, кровлю и место доставки.</p>
          </div>
          <LeadForm source="project_order" projectSlug={project.slug} title="Получить расчёт" />
        </div>
      </section>
    </main>
  );
}
