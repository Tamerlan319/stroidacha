"use client";

import Link from "next/link";
import { useState, useSyncExternalStore } from "react";

import styles from "./CookieBanner.module.css";

export const COOKIE_CONSENT_STORAGE_KEY = "brusoteka-cookie-consent";
export const COOKIE_CONSENT_EVENT = "brusoteka-cookie-consent-changed";

export type CookieConsentValue = "all" | "essential";

export function getCookieConsentSnapshot(): CookieConsentValue | null {
  if (typeof window === "undefined") {
    return null;
  }

  const value = window.localStorage.getItem(COOKIE_CONSENT_STORAGE_KEY);

  return value === "all" || value === "essential" ? value : null;
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
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const isOpen = consent === null || isSettingsOpen;

  function saveConsent(value: CookieConsentValue) {
    window.localStorage.setItem(COOKIE_CONSENT_STORAGE_KEY, value);
    window.dispatchEvent(
      new CustomEvent<CookieConsentValue>(COOKIE_CONSENT_EVENT, {
        detail: value,
      })
    );
    setIsSettingsOpen(false);
  }

  return (
    <>
      {isOpen && (
        <div className={styles.banner} role="dialog" aria-live="polite">
          <div className={styles.content}>
            <strong>Настройки cookie</strong>
            <p>
              Необходимые cookie обеспечивают работу сайта. Яндекс Метрика
              включается только после вашего согласия. Подробнее — в{" "}
              <Link href="/cookies">политике cookie</Link>.
            </p>
          </div>

          <div className={styles.actions}>
            <button type="button" onClick={() => saveConsent("essential")}>
              Только необходимые
            </button>

            <button
              className={styles.primary}
              type="button"
              onClick={() => saveConsent("all")}
            >
              Принять аналитику
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
