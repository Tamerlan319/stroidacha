"use client";

import Link from "next/link";
import { useState, useSyncExternalStore } from "react";

import {
  getServerMetrikaFrameSnapshot,
  isInsideMetrikaFrame,
  subscribeToMetrikaFrame,
} from "../lib/metrika";
import styles from "./CookieBanner.module.css";

export const COOKIE_CONSENT_STORAGE_KEY = "brusoteka-cookie-consent";
export const COOKIE_CONSENT_EVENT = "brusoteka-cookie-consent-changed";

// Баннер — уведомление, а не запрос согласия: Яндекс Метрика работает с
// первого захода (YandexMetrika.tsx). null — посетитель ещё ничего не
// выбрал, "all" — нажал «Понятно», "essential" — отказался от аналитики.
// Значения и ключ хранилища остались от прежней схемы «сначала согласие»,
// чтобы уже сделанный выбор (в том числе отказ) не сбросился.
export type CookieConsentValue = "all" | "essential";

export function getCookieConsentSnapshot(): CookieConsentValue | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const value = window.localStorage.getItem(COOKIE_CONSENT_STORAGE_KEY);
    return value === "all" || value === "essential" ? value : null;
  } catch {
    // Браузер запретил хранилище сайту — без выбора, но и без падения
    // всей страницы (снимок читается при каждом рендере).
    return null;
  }
}

export function getServerCookieConsentSnapshot(): null {
  return null;
}

export function subscribeToCookieConsent(
  onStoreChange: () => void
): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }

  const handleChange = () => {
    onStoreChange();
  };

  window.addEventListener("storage", handleChange);
  window.addEventListener(COOKIE_CONSENT_EVENT, handleChange);

  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener(COOKIE_CONSENT_EVENT, handleChange);
  };
}

export default function CookieBanner() {
  const consent = useSyncExternalStore(
    subscribeToCookieConsent,
    getCookieConsentSnapshot,
    getServerCookieConsentSnapshot
  );
  const insideMetrikaFrame = useSyncExternalStore(
    subscribeToMetrikaFrame,
    isInsideMetrikaFrame,
    getServerMetrikaFrameSnapshot
  );
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Во фрейме интерфейса Метрики страницу смотрит владелец счётчика, а не
  // посетитель (см. lib/metrika.ts) — баннер там только закрывал бы часть
  // карты кликов.
  if (insideMetrikaFrame) {
    return null;
  }

  const isOpen = consent === null || isSettingsOpen;

  function saveConsent(value: CookieConsentValue) {
    try {
      window.localStorage.setItem(COOKIE_CONSENT_STORAGE_KEY, value);
    } catch {
      // Хранилище запрещено — выбор проживёт только до перезагрузки.
    }
    window.dispatchEvent(
      new CustomEvent<CookieConsentValue>(COOKIE_CONSENT_EVENT, {
        detail: value,
      })
    );
    setIsSettingsOpen(false);

    // К моменту отказа Метрика на странице уже работает, а выгрузить
    // загруженный tag.js нельзя — убранный из дерева <Script> его не
    // останавливает. Отказ вступает в силу сразу только перезагрузкой:
    // после неё YandexMetrika счётчик уже не отрисует.
    if (value === "essential" && typeof window.ym === "function") {
      window.location.reload();
    }
  }

  return (
    <>
      {isOpen && (
        <div className={styles.banner} role="dialog" aria-live="polite">
          <div className={styles.content}>
            <strong>Мы используем cookie</strong>
            <p>
              Сайт использует cookie и Яндекс Метрику для анализа посещаемости.
              Продолжая пользоваться сайтом, вы соглашаетесь с этим. Подробнее —
              в <Link href="/cookies">политике cookie</Link>.
            </p>
          </div>

          <div className={styles.actions}>
            <button type="button" onClick={() => saveConsent("essential")}>
              Отказаться
            </button>

            <button
              className={styles.primary}
              type="button"
              onClick={() => saveConsent("all")}
            >
              Понятно
            </button>
          </div>
        </div>
      )}

      {consent !== null && !isOpen && (
        <button
          className={styles.settingsButton}
          type="button"
          onClick={() => setIsSettingsOpen(true)}
        >
          Cookie
        </button>
      )}
    </>
  );
}
