import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import HomePortfolioShowcase from "./components/HomePortfolioShowcase";
import JsonLd from "./components/JsonLd";
import LeadForm from "./components/LeadForm";
import ProjectCatalog from "./components/ProjectCatalog";
import SiteIcon from "./components/SiteIcon";
import { CATALOG_LINKS, SITE_DESCRIPTION, SITE_NAME, SITE_URL } from "./lib/site";

const HOME_TITLE = "Дома и бани из бруса под ключ — Брусодел";

export const metadata: Metadata = {
  title: { absolute: HOME_TITLE },
  description: SITE_DESCRIPTION,
  alternates: { canonical: "/" },
  openGraph: {
    title: HOME_TITLE,
    description: SITE_DESCRIPTION,
    url: "/",
    type: "website",
    locale: "ru_RU",
    siteName: SITE_NAME,
    images: [{
      url: "/images/banners/home-hero.jpg",
      width: 1672,
      height: 941,
      alt: "Строительство дома из бруса компанией Брусодел",
    }],
  },
  twitter: {
    card: "summary_large_image",
    title: HOME_TITLE,
    description: SITE_DESCRIPTION,
    images: ["/images/banners/home-hero.jpg"],
  },
};

type FAQ = { id: number; question: string; answer: string };

const defaultFaqs: FAQ[] = [
  {
    id: 1,
    question: "Сколько времени занимает строительство?",
    answer: "Небольшой объект можно собрать от 8 дней. Точный срок зависит от площади, комплектации и условий на участке и указывается в договоре.",
  },
  {
    id: 2,
    question: "Можно ли изменить готовый проект?",
    answer: "Да. Скорректируем планировку типового проекта или рассчитаем строительство по вашему эскизу, плану или фотографии.",
  },
  {
    id: 3,
    question: "Как проходит оплата?",
    answer: "Цена и этапы оплаты фиксируются в договоре. Основной платёж производится после доставки материала и бригады на участок.",
  },
  {
    id: 4,
    question: "Можно ли приехать на производство?",
    answer: "Да, визит можно согласовать с менеджером заранее. Покажем материал, оборудование и этапы подготовки домокомплекта.",
  },
];

const productionSteps = [
  {
    number: "1",
    title: "Собственное производство",
    text: "Заготавливаем древесину, сушим, профилируем и подготавливаем каждый брус.",
    image: "/images/home-v2/timber-yard.webp",
    alt: "Подготовленный строительный брус на производстве",
  },
  {
    number: "2",
    title: "Комплектуем домокомплект",
    text: "Точно размечаем и упаковываем элементы — каждая деталь готова к сборке.",
    image: "/images/home-v2/house-kit.webp",
    alt: "Профилированный брус для домокомплекта",
  },
  {
    number: "3",
    title: "Собираем на участке",
    text: "Опытная бригада работает аккуратно, соблюдает технологию и порядок на участке.",
    image: "/images/home-v2/house-assembly.webp",
    alt: "Сборка деревянного дома на участке",
  },
] as const;

const workSteps = [
  { icon: "blueprint", title: "Согласовываем проект", text: "Выберите готовый проект или пришлите свой эскиз." },
  { icon: "price", title: "Подписываем договор", text: "Фиксируем комплектацию, стоимость и сроки работ." },
  { icon: "truck", title: "Доставляем материалы", text: "Привозим домокомплект и бригаду на ваш участок." },
  { icon: "house", title: "Строим объект", text: "Собираем дом или баню с соблюдением технологии." },
  { icon: "shield", title: "Принимаете работу", text: "Проверяете результат и подписываете акт приёмки." },
] as const;

async function getFaqs(): Promise<FAQ[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return defaultFaqs;

  try {
    const response = await fetch(`${apiUrl}/homepage/`, { cache: "no-store" });
    if (!response.ok) return defaultFaqs;
    const data = await response.json();
    return data.faqs?.length ? data.faqs : defaultFaqs;
  } catch {
    return defaultFaqs;
  }
}

function buildHomeJsonLd(): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebPage",
        "@id": `${SITE_URL}/#webpage`,
        url: SITE_URL,
        name: HOME_TITLE,
        description: SITE_DESCRIPTION,
        inLanguage: "ru-RU",
        isPartOf: { "@id": `${SITE_URL}/#website` },
        about: { "@id": `${SITE_URL}/#organization` },
      },
      {
        "@type": "Service",
        "@id": `${SITE_URL}/#construction-service`,
        name: "Строительство домов и бань из бруса под ключ",
        serviceType: "Строительство деревянных домов и бань",
        description: SITE_DESCRIPTION,
        provider: { "@id": `${SITE_URL}/#organization` },
        areaServed: { "@type": "Country", name: "Россия" },
        hasOfferCatalog: {
          "@type": "OfferCatalog",
          name: "Каталог строительства",
          itemListElement: CATALOG_LINKS.map((item) => ({
            "@type": "Offer",
            itemOffered: {
              "@type": "Service",
              name: item.title,
              description: item.description,
              url: `${SITE_URL}${item.href}`,
            },
          })),
        },
      },
    ],
  };
}

export default async function HomePage() {
  const faqs = await getFaqs();

  return (
    <main className="homeEditorial">
      <JsonLd data={buildHomeJsonLd()} />

      <section className="homeHero">
        <div className="container homeHeroGrid">
          <div className="homeHeroContent">
            <h1>Строим дома,<br />в которых остаются<br />надолго</h1>
            <p className="heroText">Дома и бани из собственного бруса<br />от производителя</p>
            <div className="heroActions">
              <a href="#projects" className="buttonPrimary">Выбрать проект</a>
              <Link href="/calculator" className="buttonSecondary">Рассчитать стоимость</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="homeTrust" aria-label="О компании">
        <div className="container homeTrustGrid">
          <article><SiteIcon name="house" /><div><strong>С 2009 года</strong><span>Строим из бруса<br />для жизни</span></div></article>
          <article><SiteIcon name="factory" /><div><strong>Производство<br />в Чухломе</strong><span>Собственный профилированный брус</span></div></article>
          <article><SiteIcon name="blueprint" /><div><strong>Российские<br />плотники</strong><span>Опытные бригады из Костромской области</span></div></article>
          <article><SiteIcon name="shield" /><div><strong>Гарантия<br />3 года</strong><span>На работы и конструкцию</span></div></article>
        </div>
      </section>

      <section className="container homeSection homeDirections">
        <h2 className="homeTitle">Выберите направление</h2>
        <div className="homeDirectionGrid">
          <Link className="homeDirectionCard homeDirectionHouse" href="/doma-iz-brusa">
            <span className="directionImage" />
            <div><h3>Дома из бруса</h3><p>Для круглогодичного проживания</p><span className="roundArrow">→</span></div>
          </Link>
          <Link className="homeDirectionCard homeDirectionBath" href="/bani-iz-brusa">
            <span className="directionImage" />
            <div><h3>Бани из бруса</h3><p>Тёплые, уютные, надёжные</p><span className="roundArrow">→</span></div>
          </Link>
          <Link className="homeDirectionCard homeDirectionCustom" href="/calculator">
            <div><h3>Индивидуальный<br />проект</h3><p>Спроектируем дом или баню по вашим размерам и пожеланиям</p><span className="buttonOutline">Подробнее</span></div>
            <SiteIcon name="blueprint" className="customBlueprint" />
          </Link>
        </div>
      </section>

      <ProjectCatalog
        initialCategory="houses"
        showFilters={false}
        maxItems={6}
        eyebrow=""
        title="Проекты, которые выбирают"
        description=""
        moreHref="/doma-iz-brusa"
        moreLabel="Смотреть все проекты"
      />

      <section className="container homeSection homeProductionSteps">
        <h2 className="homeTitle">От леса до готового дома</h2>
        <div className="productionStepGrid">
          {productionSteps.map((step) => (
            <article className="productionStepCard" key={step.number}>
              <div className="productionStepImage">
                <Image src={step.image} alt={step.alt} fill sizes="(max-width: 680px) 100vw, 33vw" />
              </div>
              <div><h3>{step.number}. {step.title}</h3><p>{step.text}</p></div>
            </article>
          ))}
        </div>
      </section>

      <section className="homePortfolioBand">
        <div className="container homeSection builtProject">
          <div className="homeSectionHeading">
            <h2 className="homeTitle">Реализованный объект</h2>
            <Link href="/portfolio">Все объекты →</Link>
          </div>
          <HomePortfolioShowcase />
        </div>
      </section>

      <section className="container homeSection homePackages">
        <div className="homeSectionHeading packageHeading">
          <div>
            <span className="homeEyebrow">Готовое решение</span>
            <h2 className="homeTitle">Строительство под ключ</h2>
          </div>
          <p>Берём на себя весь цикл работ — от производства домокомплекта до тёплого дома, готового к жизни.</p>
        </div>
        <article className="packageCard packageTurnkey packageSingle">
          <div>
            <h3>Дом, в который можно заезжать</h3>
            <p>Фиксируем состав работ и материалов в договоре, организуем доставку и собираем объект на вашем участке.</p>
            <ul>
              <li>Профилированный брус камерной сушки</li>
              <li>Сборка на деревянные нагели</li>
              <li>Кровля из металлочерепицы</li>
              <li>Окна и двери</li>
              <li>Утепление, полы и потолки</li>
              <li>Доставка и монтаж</li>
            </ul>
            <Link href="/calculator" className="buttonOutline">Рассчитать стоимость</Link>
          </div>
        </article>
      </section>

      <section className="homeReliability">
        <div className="container homeSection">
          <h2 className="homeTitle">С нами — надёжно и просто</h2>
          <div className="reliabilityGrid">
            <article><SiteIcon name="price" /><div><h3>Фиксируем стоимость в договоре</h3><p>Цена не изменится в процессе строительства.</p></div></article>
            <article><SiteIcon name="shield" /><div><h3>Поэтапная оплата</h3><p>Платите по факту выполненных этапов работ.</p></div></article>
            <article><SiteIcon name="truck" /><div><h3>Доставляем по России</h3><p>Заранее рассчитываем маршрут и стоимость доставки.</p></div></article>
          </div>
        </div>
      </section>

      <section className="container homeSection homeWorkSteps">
        <div className="homeSectionHeading">
          <h2 className="homeTitle">Этапы работы</h2>
          <p>Понятный процесс от первого разговора до сдачи объекта</p>
        </div>
        <div className="editorialStepsGrid">
          {workSteps.map((step, index) => (
            <article className="editorialStep" key={step.title}>
              <div className="editorialStepTop">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <SiteIcon name={step.icon} />
              </div>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="container homeSection homeDelivery">
        <div className="homeDeliveryMap deliveryMapReal">
          <iframe
            src="https://yandex.ru/map-widget/v1/?um=constructor%3Af2357c7eef2c0a4200a5244d74da6f5e737586274d8529dba014874e07929877&source=constructor"
            title="Карта доставки Брусодел"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>
        <div className="homeDeliveryCopy">
          <p className="homeLabel">Логистика</p>
          <h2>Бесплатная доставка материала по согласованным направлениям</h2>
          <p>Для каждого проекта заранее считаем объём материалов, транспорт и условия разгрузки. Маршрут и стоимость доставки фиксируем до начала строительства.</p>
          <a className="buttonOutline" href="#consultation-form">Узнать стоимость доставки</a>
        </div>
      </section>

      <section className="homeConsultation" id="consultation-form">
        <div className="container homeSection homeConsultationGrid">
          <div className="homeConsultationCopy">
            <p className="homeLabel">Бесплатная консультация</p>
            <h2>Обсудим ваш проект по телефону и подготовим расчёт</h2>
            <p>Менеджер уточнит размеры, комплектацию и регион строительства. После разговора вы получите ориентировочную стоимость и ответы на вопросы.</p>
            <ul>
              <li>Перезвоним в удобное рабочее время</li>
              <li>Подберём проект под участок и бюджет</li>
              <li>Предварительно рассчитаем строительство и доставку</li>
            </ul>
          </div>
          <div className="homeConsultationForm">
            <LeadForm title="Записаться на консультацию и расчёт" source="home_phone_consultation" />
          </div>
        </div>
      </section>

      <section className="container homeSection homeFinal" id="lead-form">
        <div className="homeFaq">
          <h2 className="homeTitle">Ответы на частые вопросы</h2>
          <div className="faqList">
            {faqs.slice(0, 4).map((faq) => (
              <details className="faqItem" key={faq.id}><summary>{faq.question}</summary><p>{faq.answer}</p></details>
            ))}
          </div>
        </div>
        <div className="homeFinalCta">
          <h2>Готовы построить дом мечты?</h2>
          <p>Выберите проект или получите предварительный расчёт стоимости.</p>
          <div><a className="buttonPrimary" href="#projects">Выбрать проект</a><Link className="buttonSecondary" href="/calculator">Рассчитать стоимость</Link></div>
        </div>
      </section>
    </main>
  );
}
