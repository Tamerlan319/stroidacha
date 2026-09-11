import { YANDEX_METRIKA_ID } from "./site";

// Тонкая обёртка над window.ym для отправки целей (см. YandexMetrika.tsx —
// сам тег грузится только после согласия на аналитику, поэтому window.ym
// на проде есть не всегда: до согласия, в деве и т.д. — reachGoal в этих
// случаях должен молча ничего не делать, а не падать.
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

// Карта кликов/ссылок/скроллинга, аналитика форм и плеер Вебвизора
// открывают сайт во фрейме и ждут, что внутри загрузится счётчик — иначе
// пишут «Не установлен код счётчика». Согласия на cookie внутри фрейма нет
// и быть не может: хранилище фрейма отделено браузером от обычного визита
// на сайт, а смотрит страницу не посетитель, а владелец счётчика из своего
// кабинета. Какие сайты вообще могут встроить нас во фрейм, решает CSP
// frame-ancestors в caddy/Caddyfile; здесь родитель дополнительно
// сверяется с доменами Метрики, чтобы чужой сайт с iframe не мог включить
// счётчик без согласия, даже если заголовок когда-нибудь ослабят.
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
