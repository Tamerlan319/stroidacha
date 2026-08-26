export const legalConfig = {
  brandName: "Брусодел",
  legalName: "ООО «СтройДача»",
  inn: "4400020680",
  ogrn: "1244400002835",
  kpp: "440001001",
  legalAddress:
    "157130, Костромская область, м. о. Чухломский, г. Чухлома, пер. Дорожный, д. 17, кв. 2",
  workHours: "Ежедневно с 9:00 до 20:00",
  phoneDisplay: "+7 967 680-18-12",
  phoneDigits: "79676801812",
  email: "brusodel@yandex.ru",
  privacyEmail: "brusodel@yandex.ru",
  consentVersion: "2026-08-03",
  // Держите в согласии с LEAD_RETENTION_MONTHS в backend/.env.prod — это
  // просто текст политики, отдельного API для этого значения нет.
  retentionMonths: 24,
  whatsappPhone: "79676801812",
  sites: ["https://brusodel.ru", "https://stroydacha.online"],
  useYandexMetrica: true,
} as const;

export function getWhatsAppLink(message?: string) {
  const text =
    message ||
    "Здравствуйте! Хочу получить быстрый расчёт по проекту на сайте Брусодел.";

  return `https://wa.me/${legalConfig.whatsappPhone}?text=${encodeURIComponent(
    text
  )}`;
}
