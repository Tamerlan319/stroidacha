import { YANDEX_METRIKA_ID } from "./site";

// Тонкая обёртка над window.ym для отправки целей (см. YandexMetrika.tsx —
// сам тег грузится только после согласия на все cookie, поэтому window.ym
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
