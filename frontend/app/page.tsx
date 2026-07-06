import LeadForm from "./components/LeadForm";

type ProjectCategory = {
  id: number;
  title: string;
  slug: string;
};

type Project = {
  id: number;
  external_id: string | null;
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

type Advantage = {
  id: number;
  title: string;
  description: string;
  icon: string;
};

type WorkStep = {
  id: number;
  title: string;
  description: string;
};

type FAQ = {
  id: number;
  question: string;
  answer: string;
};

type Review = {
  id: number;
  author_name: string;
  city: string;
  text: string;
  project_name: string;
  rating: number;
};

type HomepageContent = {
  advantages: Advantage[];
  work_steps: WorkStep[];
  faqs: FAQ[];
  reviews: Review[];
};

async function getProjects(): Promise<Project[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/projects/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Не удалось загрузить проекты из Django API");
  }

  return response.json();
}

async function getHomepageContent(): Promise<HomepageContent> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/homepage/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Не удалось загрузить контент главной страницы");
  }

  return response.json();
}

function formatPrice(price: number | null) {
  if (!price) {
    return "Цена по запросу";
  }

  return `от ${price.toLocaleString("ru-RU")} ₽`;
}

export default async function HomePage() {
  const [projects, homepageContent] = await Promise.all([
    getProjects(),
    getHomepageContent(),
  ]);

  return (
    <main>
      <section className="hero">
        <div className="container">
          <p className="eyebrow">Дома, бани и гаражи из бруса</p>

          <h1>Строительство из дерева с собственного производства</h1>

          <p className="heroText">
            Проекты домов, бань и гаражей с понятными комплектациями,
            сроками и ценами. Работаем по региону и организуем строительство
            по России.
          </p>

          <div className="heroActions">
            <a href="#projects" className="buttonPrimary">
              Смотреть проекты
            </a>
            <a href="#lead-form" className="buttonSecondary">
              Рассчитать стоимость
            </a>
          </div>
        </div>
      </section>

      {homepageContent.advantages.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Почему выбирают нас</p>
            <h2>Собственное производство и понятная комплектация</h2>
          </div>

          <div className="advantageGrid">
            {homepageContent.advantages.map((advantage) => (
              <article className="infoCard" key={advantage.id}>
                <div className="iconBadge">{advantage.icon || "✓"}</div>
                <h3>{advantage.title}</h3>
                <p>{advantage.description}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="container section" id="projects">
        <div className="sectionHeader">
          <p className="eyebrow">Каталог</p>
          <h2>Популярные проекты</h2>
          <p>
            Выберите готовый проект или отправьте свой — менеджер поможет
            рассчитать стоимость под нужную комплектацию.
          </p>
        </div>

        <div className="projectGrid">
          {projects.map((project) => (
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

      {homepageContent.work_steps.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Как мы работаем</p>
            <h2>Этапы строительства</h2>
          </div>

          <div className="stepList">
            {homepageContent.work_steps.map((step, index) => (
              <article className="stepCard" key={step.id}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {homepageContent.reviews.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Отзывы</p>
            <h2>Что говорят клиенты</h2>
          </div>

          <div className="reviewGrid">
            {homepageContent.reviews.map((review) => (
              <article className="infoCard" key={review.id}>
                <div className="reviewRating">
                  {"★".repeat(review.rating)}
                </div>

                <p>{review.text}</p>

                <strong>{review.author_name}</strong>

                {(review.city || review.project_name) && (
                  <span className="reviewMeta">
                    {[review.city, review.project_name].filter(Boolean).join(" · ")}
                  </span>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {homepageContent.faqs.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">FAQ</p>
            <h2>Частые вопросы</h2>
          </div>

          <div className="faqList">
            {homepageContent.faqs.map((faq) => (
              <details className="faqItem" key={faq.id}>
                <summary>{faq.question}</summary>
                <p>{faq.answer}</p>
              </details>
            ))}
          </div>
        </section>
      )}

      <section className="container section" id="lead-form">
        <LeadForm title="Получить консультацию" source="callback" />
      </section>
    </main>
  );
}