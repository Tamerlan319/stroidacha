import { YANDEX_METRIKA_ID } from "./site";

// Тонкая обёртка над window.ym для отправки целей (см. YandexMetrika.tsx).
// window.ym есть не всегда — без согласия на аналитику и в деве тег не
// грузится, а у части посетителей его режут блокировщики рекламы, — reachGoal
// в этих случаях должен молча ничего не делать, а не падать.
declare global {
  interface Window {
    ym?: (...args: unknown[]) => void;
  }
}

export function reachGoal(goal: string, params?: Record<string, unknown>) {
  if (typeof window === "undefined" || typeof window.ym !== "function") {
    return;
  }

  window.ym(YANDEX_METRIKA_ID, "reachGoal", goal, params);
}

// Просмотр страницы при переходе внутри сайта. Next.js меняет страницы без
// перезагрузки, а счётчик сам видит только первую из них: без этого у любого
// визита в Метрике «1 стр.», путь человека по сайту не виден, а время на
// сайте обрывается на 0:15 — отметке accurateTrackBounce.
export function trackPageview(url: string, referer: string, title: string) {
  if (typeof window === "undefined" || typeof window.ym !== "function") {
    return;
  }

  window.ym(YANDEX_METRIKA_ID, "hit", url, { referer, title });
}

// Какой мессенджер открывает ссылка — для цели messenger_click. null — не
// мессенджер.
export function messengerPlatform(href: string): string | null {
  if (/^(whatsapp:|https?:\/\/(wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com)(\/|\?|$))/i.test(href)) {
    return "whatsapp";
  }
  if (/^(tg:|https?:\/\/(t\.me|telegram\.me)\/)/i.test(href)) {
    return "telegram";
  }
  if (/^https?:\/\/(www\.)?max\.ru(\/|$)/i.test(href)) {
    return "max";
  }
  if (/^https?:\/\/(www\.)?(vk\.com|vk\.me)(\/|$)/i.test(href)) {
    return "vk";
  }
  return null;
}

// Карта кликов, аналитика форм и плеер Вебвизора открывают сайт во фрейме и
// ждут, что внутри загрузится счётчик — иначе пишут «Не установлен код
// счётчика». Смотрит страницу там не посетитель, а владелец счётчика из
// своего кабинета, поэтому во фрейме счётчик грузится без согласия и баннер
// не показывается. Какие сайты вообще могут встроить нас во фрейм, решает
// CSP frame-ancestors в caddy/Caddyfile; здесь родитель дополнительно
// сверяется с доменами Метрики, чтобы чужой сайт с iframe не мог спрятать
// баннер и включить счётчик посетителю без согласия.
const METRIKA_FRAME_PARENT =
  /^https?:\/\/([^/]+\.)?(webvisor\.com|(metrika|metrica|metr|analytics)\.yandex(\.[a-z]{2,3}){0,2}|(metrika|metrica)\.ya\.ru)(\/|$)/;

export function isInsideMetrikaFrame(): boolean {
  if (typeof window === "undefined" || window.self === window.top) {
    return false;
  }

  // ancestorOrigins есть в Chromium и Safari; Firefox его не знает, там
  // остаётся referrer — адрес страницы, встроившей фрейм.
  const ancestors = window.location.ancestorOrigins as
    | DOMStringList
    | undefined;
  const parent =
    ancestors && ancestors.length > 0 ? ancestors[0] : document.referrer;

  return METRIKA_FRAME_PARENT.test(parent);
}

// Родитель фрейма за время жизни страницы не меняется — подписываться не
// на что, но useSyncExternalStore нужна функция подписки.
export function subscribeToMetrikaFrame(): () => void {
  return () => undefined;
}

export function getServerMetrikaFrameSnapshot(): false {
  return false;
}
