export const SITE_NAME = "Брусодел";
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL || "https://brusodel.ru"
).replace(/\/$/, "");

export const SITE_DESCRIPTION =
  "Строим дома и бани из бруса под ключ по России. Готовые проекты, собственное производство, понятные комплектации и расчёт стоимости.";

export const SITE_PHONE = "+7 967 680-18-12";
export const SITE_PHONE_HREF = "+79676801812";
export const SITE_EMAIL = "brusodel@yandex.ru";

// Страницы о компании — одинаковый список в меню шапки и в подвале.
export const COMPANY_LINKS = [
  { title: "О директоре", href: "/o-direktore" },
  { title: "Выписка из ЕГРЮЛ", href: "/vypiska-iz-egryul" },
  { title: "Производство", href: "/proizvodstvo" },
  { title: "Доставка", href: "/dostavka" },
  { title: "Маткапитал", href: "/materinskij-kapital" },
  { title: "Ипотека", href: "/ipoteka" },
];

// Счётчик Яндекс.Метрики — используется и в самом теге (YandexMetrika.tsx),
// и при отправке целей (lib/metrika.ts). Один счётчик на весь сайт, поэтому
// константа общая, а не продублирована в обоих местах.
export const YANDEX_METRIKA_ID = 111986431;

export const CATALOG_LINKS = [
  {
    title: "Дома из бруса",
    description: "Для дачи и постоянного проживания",
    href: "/doma-iz-brusa",
    icon: "house",
  },
  {
    title: "Бани из бруса",
    description: "Готовые проекты разных размеров",
    href: "/bani-iz-brusa",
    icon: "factory",
  },
] as const;
