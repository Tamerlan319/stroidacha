"use client";

import Link from "next/link";
import { useState, useSyncExternalStore } from "react";

import { saveCookieConsent, useCookieConsent } from "../lib/cookieConsent";
import {
  getServerMetrikaFrameSnapshot,
  isInsideMetrikaFrame,
  subscribeToMetrikaFrame,
} from "../lib/metrika";
import styles from "./CookieNotice.module.css";

function subscribeToNothing() {
  return () => undefined;
}

// Уведомление о cookie в углу экрана. Ничего не спрашивает: Метрика работает
// с входа на сайт (YandexMetrika.tsx), уведомление об этом сообщает. Так
// решил владелец сайта; окно с выбором (CookieBanner.tsx) сохранено и
// отключено в layout.tsx — чтобы вернуть его, поменять компонент там.
//
// «Согласен» запоминается тем же выбором "all", что и в окне: уведомление
// больше не показывается, а карты Яндекса грузятся сразу. Крестик прячет
// уведомление до перезагрузки страницы. Кто раньше нажал в окне «Только
// необходимые», уведомление не видит, и Метрика у него не работает.
export default function CookieNotice() {
  const consent = useCookieConsent();
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
  const [isClosed, setIsClosed] = useState(false);

  if (!isClient || insideMetrikaFrame || consent !== null || isClosed) {
    return null;
  }

  return (
    <aside className={styles.notice} aria-label="Уведомление о cookie">
      <button
        type="button"
        className={styles.close}
        onClick={() => setIsClosed(true)}
        aria-label="Закрыть уведомление"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 6l12 12M18 6 6 18" />
        </svg>
      </button>

      <svg className={styles.info} viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="9.5" />
        <path d="M12 11v6M12 7.5v.01" />
      </svg>

      <p>
        Мы используем файлы cookie и Яндекс.Метрику для корректной работы и
        улучшения сайта. Продолжая посещение сайта, вы соглашаетесь на
        использование <Link href="/cookies">файлов cookie</Link>.
      </p>

      <button
        type="button"
        className={styles.agree}
        onClick={() => saveCookieConsent("all")}
      >
        Согласен
      </button>
    </aside>
  );
}
