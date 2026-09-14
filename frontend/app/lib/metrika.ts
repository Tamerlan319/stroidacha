import { YANDEX_METRIKA_ID } from "./site";

// Тонкая обёртка над window.ym для отправки целей (см. YandexMetrika.tsx).
// window.ym есть не всегда — в деве тег не грузится, а у части посетителей
// его режут блокировщики рекламы, — reachGoal в этих случаях должен молча
// ничего не делать, а не падать.
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

// ClientID посетителя в Метрике — уходит вместе с заявкой, чтобы реальную
// заявку потом можно было загрузить в Метрику офлайн-конверсией (admin →
// «Выгрузить для Метрики»). Счётчик хранит его в cookie _ym_uid; если cookie
// нет — спрашиваем сам счётчик, но не дольше полсекунды, чтобы не задерживать
// отправку. Нет Метрики (блокировщик, локальная версия) — пустая строка.
export function getMetrikaClientId(timeoutMs = 500): Promise<string> {
  if (typeof window === "undefined") {
    return Promise.resolve("");
  }

  const cookie = document.cookie.match(/(?:^|;\s*)_ym_uid=(\d+)/);
  if (cookie) {
    return Promise.resolve(cookie[1]);
  }

  const ym = window.ym;
  if (typeof ym !== "function") {
    return Promise.resolve("");
  }

  return new Promise<string>((resolve) => {
    const timer = window.setTimeout(() => resolve(""), timeoutMs);
    ym(YANDEX_METRIKA_ID, "getClientID", (clientId: unknown) => {
      window.clearTimeout(timer);
      resolve(
        typeof clientId === "string" || typeof clientId === "number"
          ? String(clientId)
          : ""
      );
    });
  });
}

// Какой мессенджер открывает ссылка — для цели messenger_click. null — не
// мессенджер. ВКонтакте считается так же, как раньше считали SocialLinks.
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
