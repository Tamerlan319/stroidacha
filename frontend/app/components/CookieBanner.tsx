"use client";

import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";

import {
  type CookieConsent,
  saveCookieConsent,
  subscribeToCookieSettingsOpen,
  useCookieConsent,
} from "../lib/cookieConsent";
import {
  getServerMetrikaFrameSnapshot,
  isInsideMetrikaFrame,
  subscribeToMetrikaFrame,
} from "../lib/metrika";
import styles from "./CookieBanner.module.css";

function subscribeToNothing() {
  return () => undefined;
}

// Баннер согласия на cookie. Необходимые (выбор в этом баннере, состояние
// каталога) работают всегда; Яндекс Метрика и виджеты Яндекса — только после
// «Принять все». Обе кнопки равноценные: отказ не должен быть сложнее
// согласия. Выбор меняется ссылкой «Настройки cookie» в подвале.
export default function CookieBanner() {
  const consent = useCookieConsent();
  // На сервере и при гидратации — false: баннер не мелькает у тех, кто уже
  // выбирал, пока клиент не прочитал их выбор.
  const isClient = useSyncExternalStore(
    subscribeToNothing,
    () => true,
    () => false
  );
  const insideMetrikaFrame = useSyncExternalStore(
    subscribeToMetrikaFrame,
    isInsideMetrikaFrame,
    getServerMetrikaFrameSnapshot
  );
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(
    () => subscribeToCookieSettingsOpen(() => setIsSettingsOpen(true)),
    []
  );

  // Во фрейме интерфейса Метрики страницу смотрит владелец счётчика (см.
  // lib/metrika.ts) — баннер там только закрывал бы карту кликов.
  if (!isClient || insideMetrikaFrame) {
    return null;
  }

  if (consent !== null && !isSettingsOpen) {
    return null;
  }

  function choose(value: CookieConsent) {
    const hadAnalytics = consent === "all";
    saveCookieConsent(value);
    setIsSettingsOpen(false);

    // Загруженный счётчик Метрики выгрузить нельзя — отказ после согласия
    // вступает в силу перезагрузкой, после неё счётчик уже не загрузится.
    if (value === "necessary" && hadAnalytics) {
      window.location.reload();
    }
  }

  return (
    <div
      className={styles.banner}
      role="dialog"
      aria-labelledby="cookie-banner-title"
      aria-describedby="cookie-banner-text"
    >
      <div className={styles.content}>
        <strong id="cookie-banner-title">Файлы cookie</strong>
        <p id="cookie-banner-text">
          Необходимые cookie нужны для работы сайта. С вашего согласия мы
          включим Яндекс Метрику и карты Яндекса — они собирают данные о
          посещении. Подробнее — в{" "}
          <Link href="/cookies">политике cookie</Link>.
        </p>
        {consent !== null && (
          <p className={styles.current}>
            Сейчас:{" "}
            {consent === "all"
              ? "разрешены все cookie"
              : "только необходимые cookie"}
            .
          </p>
        )}
      </div>

      <div className={styles.actions}>
        <button type="button" onClick={() => choose("necessary")}>
          Только необходимые
        </button>
        <button
          type="button"
          className={styles.accept}
          onClick={() => choose("all")}
        >
          Принять все
        </button>
      </div>
    </div>
  );
}
