export const legalConfig = {
  brandName: "Брусотека",
  legalName: "ООО «СтройДача»",
  inn: "4400020680",
  ogrn: "1244400002835",
  kpp: "440001001",
  legalAddress:
    "157130, Костромская область, м. о. Чухломский, г. Чухлома, пер. Дорожный, д. 17, кв. 2",
  workHours: "Ежедневно с 9:00 до 20:00",
  phoneDisplay: "+7 967 680-18-12",
  phoneDigits: "79676801812",
  email: "info@brusoteka.ru",
  privacyEmail: "info@brusoteka.ru",
  consentVersion: "2026-08-03",
  whatsappPhone: "79676801812",
  sites: ["https://brusoteka.ru", "https://stroydacha.online"],
  useYandexMetrica: true,
} as const;

export function getWhatsAppLink(message?: string) {
  const text =
    message ||
    "Здравствуйте! Хочу получить быстрый расчёт по проекту на сайте Брусотека.";

  return `https://wa.me/${legalConfig.whatsappPhone}?text=${encodeURIComponent(
    text
  )}`;
}
