import Link from "next/link";

import styles from "./LandingHeroFacts.module.css";
import SiteIcon from "./SiteIcon";

type LandingHeroFactsProps = {
  // Минимальная цена в каталоге этой категории; null — не показываем.
  minPrice: number | null;
};

type Fact = {
  icon: string;
  title: string;
  // Короткая подпись для телефона: там плашки в две колонки без пояснений.
  shortTitle?: string;
  text: string;
  href?: string;
};

function CheckIcon() {
  return (
    <svg className={styles.icon} viewBox="0 0 24 24" aria-hidden="true">
      <path d="m5 12.5 4.5 4.5L19 7.5" />
    </svg>
  );
}

// Короткие факты под заголовком страницы каталога. Человек с рекламы по
// запросу «баня из бруса под ключ цена» раньше не видел на первом экране ни
// цены, ни того, почему компании можно доверять — только общий текст. Факты
// те же, что в блоке доверия на главной (app/page.tsx); цена — за комплект
// материалов, как в карточках каталога. Ипотека и надёжная сделка — ссылки
// на подробности: страницу об ипотеке и сведения о компании из ЕГРЮЛ.
export default function LandingHeroFacts({ minPrice }: LandingHeroFactsProps) {
  const facts: Fact[] = [
    ...(minPrice
      ? [
          {
            icon: "price",
            title: `от ${minPrice.toLocaleString("ru-RU")} ₽`,
            text: "за комплект материалов",
          },
        ]
      : []),
    {
      icon: "check",
      title: "Строительство в ипотеку",
      shortTitle: "Можно в ипотеку",
      text: "",
      href: "/ipoteka",
    },
    {
      icon: "contract",
      title: "Надёжная сделка",
      text: "о компании",
      href: "/vypiska-iz-egryul",
    },
    { icon: "factory", title: "Своё производство", text: "в Чухломе" },
    { icon: "shield", title: "Гарантия 3 года", text: "на работы" },
  ];

  return (
    <ul className={styles.facts}>
      {facts.map((fact) => {
        const content = (
          <>
            {fact.icon === "check" ? (
              <CheckIcon />
            ) : (
              <SiteIcon name={fact.icon} className={styles.icon} />
            )}
            <span className={styles.label}>
              {fact.shortTitle ? (
                <>
                  <strong className={styles.fullTitle}>{fact.title}</strong>
                  <strong className={styles.shortTitle}>{fact.shortTitle}</strong>
                </>
              ) : (
                <strong>{fact.title}</strong>
              )}
              {fact.text && <span className={styles.detail}> {fact.text}</span>}
              {fact.href && <span className={styles.arrow} aria-hidden="true"> →</span>}
            </span>
          </>
        );

        return (
          <li key={fact.title} className={fact.href ? styles.linkFact : undefined}>
            {fact.href ? <Link href={fact.href}>{content}</Link> : content}
          </li>
        );
      })}
    </ul>
  );
}
