import type { Metadata } from "next";

import LeadForm from "../components/LeadForm";
import PortfolioList, { PortfolioItem } from "../components/PortfolioList";

const description =
  "Примеры построенных домов и бань из бруса: фото объектов, характеристики, материалы и стоимость строительства.";

export const metadata: Metadata = {
  title: "Портфолио построенных домов и бань",
  description,
  alternates: {
    canonical: "/portfolio",
  },
  openGraph: {
    title: "Портфолио построенных домов и бань | Брусодел",
    description,
    url: "/portfolio",
    type: "website",
    locale: "ru_RU",
    siteName: "Брусодел",
    images: ["/images/banners/home-hero.jpg"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Портфолио построенных домов и бань | Брусодел",
    description,
    images: ["/images/banners/home-hero.jpg"],
  },
};

type PortfolioApiImage = {
  id: number;
  image: string | null;
  caption: string;
  alt_text: string;
  sort_order: number;
};

type PortfolioApiProject = {
  id: number;
  title: string;
  slug: string;
  location: string;
  area: string;
  size_text: string;
  material: string;
  price: string | number | null;
  short_description: string;
  description: string;
  main_image: string | null;
  images: PortfolioApiImage[];
  sort_order: number;
  created_at: string;
};

async function getPortfolioProjects(): Promise<PortfolioApiProject[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/portfolio/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

function formatPrice(price: string | number | null) {
  if (!price) {
    return "Стоимость по запросу";
  }

  const numericPrice = Number(price);

  if (Number.isNaN(numericPrice)) {
    return "Стоимость по запросу";
  }

  return `${numericPrice.toLocaleString("ru-RU")} ₽`;
}

function mapPortfolioProject(project: PortfolioApiProject): PortfolioItem {
  const fallbackImage = "/images/banners/home-hero.jpg";
  const mainImage = project.main_image || fallbackImage;

  const galleryImages = [
    {
      id: `${project.id}-main`,
      src: mainImage,
      alt: project.title,
      caption: "",
    },
    ...(project.images || [])
      .filter((image) => image.image)
      .map((image) => ({
        id: image.id,
        src: image.image || fallbackImage,
        alt: image.alt_text || image.caption || project.title,
        caption: image.caption,
      })),
  ];

  return {
    id: project.id,
    title: project.title,
    location: project.location || "Локация уточняется",
    description:
      project.short_description ||
      project.description ||
      "Описание объекта скоро появится.",
    area: project.area || "—",
    size: project.size_text || "—",
    material: project.material || "—",
    price: formatPrice(project.price),
    mainImage,
    images: galleryImages,
  };
}

export default async function PortfolioPage() {
  const portfolioProjects = await getPortfolioProjects();
  const items = portfolioProjects.map(mapPortfolioProject);

  return (
    <main className="portfolioPage">
      <section className="portfolioHero">
        <div className="container">
          <p className="eyebrow">Портфолио</p>

          <h1>Построенные дома и бани из бруса</h1>

          <p className="heroText">
            Примеры реализованных объектов с фотографиями, характеристиками,
            материалами и ориентировочной стоимостью строительства.
          </p>
        </div>
      </section>

      <section className="container section portfolioSection">
        <div className="sectionHeader sectionHeaderRow">
          <div>
            <p className="eyebrow">Наши работы</p>
            <h2>Реализованные объекты</h2>
            <p>
              Объекты добавляются через Django-админку. Нажмите на стрелку под
              объектом, чтобы открыть фотографии.
            </p>
          </div>
        </div>

        {items.length > 0 ? (
          <PortfolioList items={items} />
        ) : (
          <div className="catalogState">
            Пока в портфолио нет активных объектов. Добавьте их в Django admin:
            Content → Портфолио.
          </div>
        )}
      </section>

      <section className="container section" id="lead-form">
        <LeadForm
          title="Хотите похожий объект?"
          source="contact_form"
          projectSlug=""
        />
      </section>
    </main>
  );
}
