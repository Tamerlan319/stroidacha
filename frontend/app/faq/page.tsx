import type { Metadata } from "next";

import LeadForm from "../components/LeadForm";
import { SITE_NAME, SITE_URL } from "../lib/site";

type FAQ = {
  id: number;
  question: string;
  answer: string;
  sort_order: number;
};

type HomepageContent = {
  faqs?: FAQ[];
};

export const metadata: Metadata = {
  title: `Вопросы и ответы — ${SITE_NAME}`,
  description:
    "Ответы на частые вопросы о проектах, комплектации, сроках, оплате, доставке и строительстве домов и бань из бруса.",
  alternates: { canonical: `${SITE_URL}/faq` },
};

async function getFaqs(): Promise<FAQ[]> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/homepage/`,
      { cache: "no-store" }
    );
    if (!response.ok) return [];
    const data = (await response.json()) as HomepageContent;
    return (data.faqs || []).sort((a, b) => a.sort_order - b.sort_order);
  } catch {
    return [];
  }
}

export default async function FaqPage() {
  const faqs = await getFaqs();

  return (
    <main className="faqPage">
      <section className="faqHero">
        <div className="container faqHeroInner">
          <p className="eyebrow">Помогаем разобраться</p>
          <h1>Частые вопросы о строительстве</h1>
          <p>
            Коротко и по делу отвечаем на вопросы о проектах, материалах,
            комплектации, оплате и организации работ на участке.
          </p>
        </div>
      </section>

      <section className="container section faqSection">
        <div className="sectionHeader">
          <p className="eyebrow">Вопросы и ответы</p>
          <h2>Что важно знать до начала работ</h2>
        </div>

        {faqs.length > 0 ? (
          <div className="faqEditorialList">
            {faqs.map((item, index) => (
              <details className="faqEditorialItem" key={item.id} open={index === 0}>
                <summary>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{item.question}</strong>
                  <i aria-hidden="true">+</i>
                </summary>
                <div>{item.answer}</div>
              </details>
            ))}
          </div>
        ) : (
          <div className="reviewsEmpty">
            Вопросы появятся после добавления записей в разделе FAQ в Django Admin.
          </div>
        )}
      </section>

      <section className="faqLeadSection" id="lead-form">
        <div className="container reviewsLeadGrid">
          <div>
            <p className="eyebrow">Остались вопросы?</p>
            <h2>Разберём ваш проект лично</h2>
            <p>
              Расскажем о вариантах строительства и подготовим предварительный
              расчёт без скрытых обязательств.
            </p>
          </div>
          <LeadForm source="faq_page" title="Задать вопрос" />
        </div>
      </section>
    </main>
  );
}
