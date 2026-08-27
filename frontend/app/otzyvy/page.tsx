import type { Metadata } from "next";

import LeadForm from "../components/LeadForm";
import YandexReviewsWidget from "../components/YandexReviewsWidget";
import { SITE_URL } from "../lib/site";

type Review = {
  id: number;
  author_name: string;
  city: string;
  text: string;
  project_name: string;
  rating: number;
};

export const metadata: Metadata = {
  // См. комментарий в app/faq/page.tsx — бренд добавляет шаблон title в
  // layout.tsx, дописывать его тут второй раз не нужно.
  title: "Отзывы клиентов",
  description:
    "Отзывы клиентов о строительстве домов и бань из бруса: сроки, качество работ и впечатления от готовых объектов.",
  alternates: { canonical: `${SITE_URL}/otzyvy` },
};

async function getReviews(): Promise<Review[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const response = await fetch(`${apiUrl}/reviews/`, { cache: "no-store" });
  if (!response.ok) return [];
  return response.json();
}

export default async function ReviewsPage() {
  const reviews = await getReviews();

  return (
    <main className="reviewsPage">
      <section className="reviewsHero">
        <div className="container reviewsHeroInner">
          <p className="eyebrow">Опыт наших клиентов</p>
          <h1>Отзывы о построенных домах и банях</h1>
          <p>
            Собрали впечатления владельцев после проектирования, строительства
            и переезда. Все тексты доступны для редактирования в Django Admin.
          </p>
          <div className="reviewsHeroFacts">
            <span><strong>{reviews.length}</strong> опубликованных отзывов</span>
            <span><strong>С 1999 года</strong> строим из бруса</span>
          </div>
        </div>
      </section>

      <section className="container section reviewsSection">
        <div className="sectionHeader">
          <p className="eyebrow">Говорят заказчики</p>
          <h2>Истории владельцев</h2>
          <p>Отзывы перенесены с прежнего сайта компании без изменения смысла.</p>
        </div>

        {reviews.length > 0 ? (
          <div className="reviewsEditorialGrid">
            {reviews.map((review, index) => (
              <article className="reviewEditorialCard" key={review.id}>
                <div className="reviewQuoteMark" aria-hidden="true">“</div>
                <p>{review.text}</p>
                <footer>
                  <span className="reviewAvatar" aria-hidden="true">
                    {review.author_name.slice(0, 1)}
                  </span>
                  <div>
                    <strong>{review.author_name}</strong>
                    {review.city && <small>{review.city}</small>}
                    {review.project_name && <em>{review.project_name}</em>}
                  </div>
                  <span className="reviewNumber">{String(index + 1).padStart(2, "0")}</span>
                </footer>
              </article>
            ))}
          </div>
        ) : (
          <div className="reviewsEmpty">
            Отзывы появятся здесь после команды импорта или добавления в Django Admin.
          </div>
        )}
      </section>

      <section className="container section reviewsSection">
        <div className="sectionHeader">
          <p className="eyebrow">Проверено Яндексом</p>
          <h2>Отзывы на Яндекс Картах</h2>
          <p>
            Рейтинг и отзывы, которые клиенты оставляют напрямую на Яндексе —
            обновляются автоматически, без нашего участия.
          </p>
        </div>

        <YandexReviewsWidget />
      </section>

      <section className="reviewsLeadSection" id="lead-form">
        <div className="container reviewsLeadGrid">
          <div>
            <p className="eyebrow">Начнём с расчёта</p>
            <h2>Обсудим ваш будущий дом</h2>
            <p>
              Подберём проект, расскажем о комплектации и подготовим понятную
              предварительную смету.
            </p>
          </div>
          <LeadForm source="reviews_page" title="Получить консультацию" />
        </div>
      </section>
    </main>
  );
}
