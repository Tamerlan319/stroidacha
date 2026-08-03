"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import styles from "./CookieBanner.module.css";

export const COOKIE_CONSENT_STORAGE_KEY = "brusoteka-cookie-consent";
export const COOKIE_CONSENT_EVENT = "brusoteka-cookie-consent-changed";

type ConsentValue = "all" | "essential";

export default function CookieBanner() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasChoice, setHasChoice] = useState(false);

  useEffect(() => {
    const currentValue = window.localStorage.getItem(
      COOKIE_CONSENT_STORAGE_KEY
    );

    setHasChoice(Boolean(currentValue));
    setIsOpen(!currentValue);
  }, []);

  function saveConsent(value: ConsentValue) {
    window.localStorage.setItem(COOKIE_CONSENT_STORAGE_KEY, value);
    window.dispatchEvent(
      new CustomEvent(COOKIE_CONSENT_EVENT, {
        detail: value,
      })
    );
    setHasChoice(true);
    setIsOpen(false);
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

      {hasChoice && !isOpen && (
        <button
          className={styles.settingsButton}
          type="button"
          onClick={() => setIsOpen(true)}
        >
          Cookie
        </button>
      )}
    </>
  );
}
