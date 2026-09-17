import { useSyncExternalStore } from "react";

import { COOKIE_CONSENT_STORAGE_KEY } from "./cookieConsentKey";

// Выбор посетителя в баннере cookie (components/CookieBanner.tsx):
// "all" — согласился на аналитику (Яндекс Метрика, виджеты Яндекса),
// "necessary" — только необходимые, null — ещё не выбирал.
//
// Без согласия Метрика не грузится вовсе (YandexMetrika.tsx), а карты Яндекса
// показываются только по нажатию (ContactMap.tsx, DeliveryMap.tsx). Ключ новый: прежний
// баннер «Понятно» был уведомлением, а не согласием, поэтому выбор спросим
// у всех заново.
export type CookieConsent = "all" | "necessary";

const CONSENT_CHANGED_EVENT = "brusodel-cookie-consent-changed";
const OPEN_SETTINGS_EVENT = "brusodel-cookie-settings-open";

export function readCookieConsent(): CookieConsent | null {
  if (typeof window === "undefined") return null;

  try {
    const value = window.localStorage.getItem(COOKIE_CONSENT_STORAGE_KEY);
    return value === "all" || value === "necessary" ? value : null;
  } catch {
    // Хранилище запрещено браузером — выбора нет, но страница не падает.
    return null;
  }
}

export function saveCookieConsent(value: CookieConsent) {
  try {
    window.localStorage.setItem(COOKIE_CONSENT_STORAGE_KEY, value);
  } catch {
    // Выбор проживёт только до перезагрузки страницы.
  }
  window.dispatchEvent(new Event(CONSENT_CHANGED_EVENT));
}

function subscribeToCookieConsent(onChange: () => void) {
  window.addEventListener("storage", onChange);
  window.addEventListener(CONSENT_CHANGED_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(CONSENT_CHANGED_EVENT, onChange);
  };
}

// На сервере выбор неизвестен — null, то есть «без согласия»: ничего
// стороннего не рендерится раньше, чем клиент прочитает выбор.
export function useCookieConsent(): CookieConsent | null {
  return useSyncExternalStore(
    subscribeToCookieConsent,
    readCookieConsent,
    () => null
  );
}

// «Настройки cookie» в подвале снова открывают баннер.
export function openCookieSettings() {
  window.dispatchEvent(new Event(OPEN_SETTINGS_EVENT));
}

export function subscribeToCookieSettingsOpen(onOpen: () => void) {
  window.addEventListener(OPEN_SETTINGS_EVENT, onOpen);
  return () => window.removeEventListener(OPEN_SETTINGS_EVENT, onOpen);
}
