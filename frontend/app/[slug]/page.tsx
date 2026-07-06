import type { Metadata } from "next";
import { notFound } from "next/navigation";

import LeadForm from "../components/LeadForm";

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

function formatPrice(price: number | null) {
  if (!price) {
    return "Цена по запросу";
  }

  return `от ${price.toLocaleString("ru-RU")} ₽`;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = await getLandingPage(slug);

  if (!page) {
    return {};
  }

  return {
    title: page.seo_title || page.h1,
    description: page.seo_description || page.intro_text,
  };
}

export default async function LandingPageRoute({ params }: PageProps) {
  const { slug } = await params;
  const page = await getLandingPage(slug);

  if (!page) {
    notFound();
  }

  return (
    <main>
      <section className="landingHero">
        <div className="container">
          <p className="eyebrow">
            {page.category?.title || "Строительство из дерева"}
          </p>

          <h1>{page.h1}</h1>

          {page.intro_text && <p className="heroText">{page.intro_text}</p>}

          <div className="heroActions">
            <a href="#projects" className="buttonPrimary">
              Смотреть проекты
            </a>
            <a href="#lead-form" className="buttonSecondary">
              Получить расчёт
            </a>
          </div>
        </div>
      </section>

      {page.related_projects.length > 0 && (
        <section className="container section" id="projects">
          <div className="sectionHeader">
            <p className="eyebrow">Подборка</p>
            <h2>Проекты по теме</h2>
            <p>
              Ниже собраны проекты, подходящие под эту страницу. Стоимость может
              меняться в зависимости от комплектации, фундамента, кровли и
              региона строительства.
            </p>
          </div>

          <div className="projectGrid">
            {page.related_projects.map((project) => (
              <article className="projectCard" key={project.id}>
                <div className="projectImage">
                  {project.main_image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={project.main_image} alt={project.title} />
                  ) : (
                    <div className="imagePlaceholder">Фото проекта</div>
                  )}
                </div>

                <div className="projectBody">
                  <div className="projectTop">
                    <span>{project.category.title}</span>
                    <span>{project.size_text || "Размер уточняется"}</span>
                  </div>

                  <h3>{project.title}</h3>

                  <p>
                    {project.short_description ||
                      "Описание проекта скоро появится."}
                  </p>

                  <div className="projectSpecs">
                    {project.area && <span>{project.area} м²</span>}
                    {project.floor_label && <span>{project.floor_label}</span>}
                  </div>

                  <div className="projectFooter">
                    <strong>{formatPrice(project.price_from)}</strong>
                    <a href={`/projects/${project.slug}`}>Подробнее</a>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
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