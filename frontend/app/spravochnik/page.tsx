import type { Metadata } from "next";
import Link from "next/link";

import { SITE_NAME } from "../lib/site";

type GuidePage = {
  id: number;
  title: string;
  slug: string;
  h1: string;
  page_type: string;
  seo_description: string;
  sort_order: number;
};

export const metadata: Metadata = {
  title: `Справочник по строительству домов из бруса | ${SITE_NAME}`,
  description:
    "Полезные статьи о выборе бруса, строительстве, эксплуатации домов и бань, финансировании и работе компании Брусотека.",
  alternates: { canonical: "/spravochnik" },
};

async function getGuidePages(): Promise<GuidePage[]> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/landing-pages/`,
      { cache: "no-store" }
    );
    if (!response.ok) return [];
    const pages = (await response.json()) as GuidePage[];
    return pages
      .filter((page) => page.page_type === "guide")
      .sort((a, b) => a.sort_order - b.sort_order);
  } catch {
    return [];
  }
}

export default async function GuideIndexPage() {
  const pages = await getGuidePages();

  return (
    <main className="guideIndexPage">
      <section className="guideIndexHero">
        <div className="container">
          <p className="eyebrow">Справочник</p>
          <h1>Полезно знать о домах и банях из бруса</h1>
          <p>
            Практические материалы о выборе древесины, строительстве,
            комплектациях, финансировании и эксплуатации деревянного дома.
          </p>
        </div>
      </section>

      <section className="container section">
        {pages.length > 0 ? (
          <div className="guideArticleGrid">
            {pages.map((page) => (
              <article className="guideArticleCard" key={page.id}>
                <p className="eyebrow">Статья</p>
                <h2>{page.h1 || page.title}</h2>
                {page.seo_description && <p>{page.seo_description}</p>}
                <Link href={`/${page.slug}`}>Читать статью →</Link>
              </article>
            ))}
          </div>
        ) : (
          <div className="catalogState">
            Статьи готовятся. Добавьте первую публикацию в Django Admin:
            SEO → SEO-страницы → тип «Справочник».
          </div>
        )}
      </section>
    </main>
  );
}
