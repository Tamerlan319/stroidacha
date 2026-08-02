export const SITE_NAME = "Брусотека";
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL || "https://brusoteka.ru"
).replace(/\/$/, "");

export const SITE_DESCRIPTION =
  "Строим дома и бани из бруса под ключ по России. Готовые проекты, собственное производство, понятные комплектации и расчёт стоимости.";

export const SITE_PHONE = "+7 967 680-18-12";
export const SITE_PHONE_HREF = "+79676801812";
export const SITE_EMAIL = "info@brusoteka.ru";

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
