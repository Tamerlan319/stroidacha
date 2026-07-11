import Link from "next/link";

import LeadForm from "./components/LeadForm";
import ProjectCatalog from "./components/ProjectCatalog";

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

type LandingPage = {
  id: number;
  title: string;
  slug: string;
  h1: string;
  page_type: string;
};

const fallbackAdvantages = [
  {
    id: 1,
    title: "84+ проекта",
    description: "Готовые решения для домов, бань, срубов и гаражей.",
    icon: "⌂",
  },
  {
    id: 2,
    title: "500+ построек",
    description: "Помогаем подобрать комплектацию под задачу и бюджет.",
    icon: "▣",
  },
  {
    id: 3,
    title: "Доставка по России",
    description: "Считаем логистику и материалы до старта строительства.",
    icon: "↗",
  },
  {
    id: 4,
    title: "Собственное производство",
    description: "Контролируем качество древесины и комплектующих.",
    icon: "♨",
  },
];

const fallbackSteps = [
  { id: 1, title: "Консультация", description: "Уточняем участок, пожелания, сроки и примерный бюджет." },
  { id: 2, title: "Проектирование", description: "Подбираем готовый проект или адаптируем планировку." },
  { id: 3, title: "Расчёт сметы", description: "Фиксируем комплектацию, материалы, доставку и работы." },
  { id: 4, title: "Производство", description: "Готовим домокомплект и согласуем дату доставки." },
  { id: 5, title: "Строительство", description: "Собираем объект на участке и ведём контроль этапов." },
  { id: 6, title: "Сдача объекта", description: "Передаём результат и рекомендации по эксплуатации." },
];

async function getHomepageContent(): Promise<HomepageContent> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  try {
    const response = await fetch(`${apiUrl}/homepage/`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Не удалось загрузить контент главной страницы");
    }

    return response.json();
  } catch {
    return {
      advantages: fallbackAdvantages,
      work_steps: fallbackSteps,
      faqs: [],
      reviews: [],
    };
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

export default async function HomePage() {
  const [homepageContent, landingPages] = await Promise.all([
    getHomepageContent(),
    getLandingPages(),
  ]);

  const advantages = homepageContent.advantages.length
    ? homepageContent.advantages
    : fallbackAdvantages;

  const workSteps = homepageContent.work_steps.length
    ? homepageContent.work_steps
    : fallbackSteps;

  return (
    <main>
      <section className="homeHero">
        <div className="container homeHeroGrid">
          <div className="homeHeroContent">
            <p className="heroKicker">Собственное производство</p>
            <h1>Дома и бани из бруса под ключ</h1>
            <p className="heroText">
              Подберём готовый проект, рассчитаем комплектацию и доставку.
              Строим дома, бани, срубы и гаражи с понятной сметой до начала работ.
            </p>

            <div className="heroActions">
              <a href="#lead-form" className="buttonPrimary">
                Рассчитать стоимость
              </a>
              <a href="#projects" className="buttonSecondary">
                Смотреть проекты
              </a>
            </div>

            <div className="heroStats">
              <span>
                <strong>500+</strong>
                построенных объектов
              </span>
              <span>
                <strong>84+</strong>
                готовых проекта
              </span>
              <span>
                <strong>7 лет</strong>
                опыта строительства
              </span>
            </div>
          </div>

          <div className="heroLeadCard">
            <LeadForm title="Бесплатный расчёт стоимости" source="callback" />
          </div>
        </div>
      </section>

      <section className="container trustStrip" aria-label="Преимущества">
        {advantages.slice(0, 4).map((advantage) => (
          <article className="trustItem" key={advantage.id}>
            <span>{advantage.icon || "⌂"}</span>
            <div>
              <strong>{advantage.title}</strong>
              <p>{advantage.description}</p>
            </div>
          </article>
        ))}
      </section>

      <ProjectCatalog
        initialCategory="houses"
        showFilters={false}
        maxItems={4}
        eyebrow="Рекомендуемые проекты"
        title="Готовые проекты домов"
        description="Популярные проекты домов из бруса для дачи и круглогодичного проживания."
        moreHref="/doma-iz-brusa"
        moreLabel="Смотреть все дома"
      />

      <ProjectCatalog
        initialCategory="baths"
        showFilters={false}
        maxItems={4}
        eyebrow="Рекомендуемые проекты"
        title="Готовые проекты бань"
        description="Готовые проекты бань из бруса с разными размерами, планировками и комплектациями."
        moreHref="/bani-iz-brusa"
        moreLabel="Смотреть все бани"
      />

      <section className="container section">
        <div className="calcBanner">
          <div>
            <p className="eyebrow">Расчёт стоимости</p>
            <h2>Поможем рассчитать дом под ваш участок</h2>
            <p>
              Уточним размер, материал, фундамент, кровлю и доставку. После этого
              подготовим понятную смету по комплектации.
            </p>
          </div>

          <div className="calcOptions">
            <span>Тип постройки</span>
            <span>Размер дома</span>
            <span>Фундамент</span>
            <span>Материал</span>
          </div>

          <Link className="buttonPrimary" href="#lead-form">
            Получить расчёт
          </Link>
        </div>
      </section>

      <section className="container section">
        <div className="sectionHeader">
          <p className="eyebrow">Как мы работаем</p>
          <h2>От консультации до сдачи объекта</h2>
        </div>

        <div className="processLine">
          {workSteps.slice(0, 6).map((step, index) => (
            <article className="processStep" key={step.id}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      {landingPages.length > 0 && (
        <section className="container section sectionCompact">
          <div className="sectionHeader sectionHeaderRow">
            <div>
              <p className="eyebrow">Разделы каталога</p>
              <h2>Выберите направление строительства</h2>
            </div>
            <Link className="textLink" href="/doma-iz-brusa">
              Перейти в каталог
            </Link>
          </div>

          <div className="seoLinkGrid">
            {landingPages.slice(0, 6).map((page) => (
              <Link className="seoLinkCard" href={`/${page.slug}`} key={page.id}>
                <span>{page.page_type}</span>
                <strong>{page.h1 || page.title}</strong>
              </Link>
            ))}
          </div>
        </section>
      )}

        <section className="container section">
          <div className="deliverySection">
            <div className="deliveryMap deliveryMapReal">
              <iframe
                src="https://yandex.ru/map-widget/v1/?um=constructor%3Af2357c7eef2c0a4200a5244d74da6f5e737586274d8529dba014874e07929877&source=constructor"
                title="Карта доставки Домодел44"
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </div>

            <div className="deliveryText">
              <p className="eyebrow">Логистика</p>

              <h2>Бесплатная доставка материала по согласованным направлениям</h2>

              <p>
                Для каждого проекта заранее считаем объём материалов, транспорт и
                условия разгрузки. Это помогает избежать сюрпризов в смете.
              </p>

              <a className="buttonGhost" href="#lead-form">
                Узнать стоимость доставки
              </a>
            </div>
          </div>
        </section>

      {homepageContent.reviews.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Отзывы</p>
            <h2>Что говорят клиенты</h2>
          </div>

          <div className="reviewGrid">
            {homepageContent.reviews.map((review) => (
              <article className="infoCard" key={review.id}>
                <div className="reviewRating">{"★".repeat(review.rating)}</div>
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
