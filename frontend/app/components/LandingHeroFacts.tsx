import styles from "./LandingHeroFacts.module.css";
import SiteIcon from "./SiteIcon";

type LandingHeroFactsProps = {
  // Минимальная цена в каталоге этой категории; null — не показываем.
  minPrice: number | null;
};

// Короткие факты под заголовком страницы каталога. Человек с рекламы по
// запросу «баня из бруса под ключ цена» раньше не видел на первом экране ни
// цены, ни того, почему компании можно доверять — только общий текст. Факты
// те же, что в блоке доверия на главной (app/page.tsx); цена — за комплект
// материалов, как в карточках каталога.
export default function LandingHeroFacts({ minPrice }: LandingHeroFactsProps) {
  const facts = [
    ...(minPrice
      ? [
          {
            icon: "price",
            title: `от ${minPrice.toLocaleString("ru-RU")} ₽`,
            text: "за комплект материалов",
          },
        ]
      : []),
    { icon: "house", title: "С 2009 года", text: "строим из бруса" },
    { icon: "factory", title: "Своё производство", text: "в Чухломе" },
    { icon: "shield", title: "Гарантия 3 года", text: "на работы и конструкцию" },
  ];

  return (
    <ul className={styles.facts}>
      {facts.map((fact) => (
        <li key={fact.title}>
          <SiteIcon name={fact.icon} className={styles.icon} />
          <span>
            <strong>{fact.title}</strong> {fact.text}
          </span>
        </li>
      ))}
    </ul>
  );
}
