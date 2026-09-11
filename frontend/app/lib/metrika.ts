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
