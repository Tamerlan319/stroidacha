"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

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

// Документы, которые человек может захотеть прочитать до выбора. Здесь окно
// не закрывает текст — выбор предлагается плашкой в углу.
const LEGAL_PATHS = new Set(["/cookies", "/privacy", "/consent-personal-data"]);

// Выбор cookie. Необходимые (выбор в этом окне, состояние каталога) работают
// всегда; Яндекс Метрика — с входа на сайт, пока не нажали «Только
// необходимые» (YandexMetrika.tsx); виджеты Яндекса — после «Принять все».
// Обе кнопки равноценные: отказ не сложнее согласия. Выбор меняется ссылкой
// «Настройки cookie» в подвале.
//
// Окно модальное: пока человек не выбрал, сайтом пользоваться нельзя.
// Плашка в углу, которую можно не замечать, оставляла без выбора почти всех —
// в Метрике было видно 6 визитов из Директа на 51 клик, и стратегия Директа
// не видела заявок с рекламы.
export default function CookieBanner() {
  const consent = useCookieConsent();
  const pathname = usePathname();
  // На сервере и при гидратации — false: окно не мелькает у тех, кто уже
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
  const dialogRef = useRef<HTMLDivElement>(null);

  // Во фрейме интерфейса Метрики страницу смотрит владелец счётчика (см.
  // lib/metrika.ts) — окно там только закрывало бы карту кликов.
  const isVisible =
    isClient && !insideMetrikaFrame && (consent === null || isSettingsOpen);
  const isBlocking = isVisible && !LEGAL_PATHS.has(pathname);
  // Закрыть без выбора можно только повторно открытые настройки: выбор уже
  // сделан, человек просто передумал его менять.
  const canDismiss = consent !== null;

  useEffect(
    () => subscribeToCookieSettingsOpen(() => setIsSettingsOpen(true)),
    []
  );

  useEffect(() => {
    if (!isBlocking) return;

    const html = document.documentElement;
    const previousOverflow = html.style.overflow;
    html.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && canDismiss) {
        setIsSettingsOpen(false);
        return;
      }

      if (event.key !== "Tab") return;

      // Фокус с клавиатуры не уходит на страницу под окном.
      const dialog = dialogRef.current;
      const focusable = dialog?.querySelectorAll<HTMLElement>("a[href], button");
      if (!dialog || !focusable || focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      const outside = active === dialog || !dialog.contains(active);

      if (event.shiftKey && (outside || active === first)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (outside || active === last)) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    const focusFrame = window.requestAnimationFrame(() => {
      dialogRef.current?.focus({ preventScroll: true });
    });

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      window.cancelAnimationFrame(focusFrame);
      html.style.overflow = previousOverflow;
    };
  }, [isBlocking, canDismiss]);

  if (!isVisible) {
    return null;
  }

  function choose(value: CookieConsent) {
    const metrikaLoaded = typeof window.ym === "function";
    saveCookieConsent(value);
    setIsSettingsOpen(false);

    // Метрика грузится при входе (YandexMetrika.tsx), а загруженный счётчик
    // выгрузить нельзя — отказ вступает в силу перезагрузкой, после неё
    // счётчик уже не загрузится.
    if (value === "necessary" && metrikaLoaded) {
      window.location.reload();
    }
  }

  const panel = (
    <div
      ref={dialogRef}
      className={isBlocking ? styles.dialog : styles.banner}
      role="dialog"
      aria-modal={isBlocking || undefined}
      aria-labelledby="cookie-banner-title"
      aria-describedby="cookie-banner-text"
      tabIndex={-1}
    >
      <div className={styles.content}>
        <strong id="cookie-banner-title">Файлы cookie</strong>
        {/* Метрика уже работает с входа на сайт (YandexMetrika.tsx), а
            «Только необходимые» её действительно отключает. Кнопка отказа,
            которая ничего не выключает, была бы обманом посетителя. */}
        <p id="cookie-banner-text">
          Сайт использует cookie-файлы, чтобы сделать ваше пребывание на нём
          максимально удобным. К сайту подключён сервис веб-аналитики
          Яндекс.Метрика, использующий cookie-файлы. Оставаясь на сайте, вы
          даёте своё{" "}
          <Link href="/cookies">согласие на обработку персональных данных</Link>{" "}
          в порядке, указанном в{" "}
          <Link href="/privacy">Политике обработки персональных данных</Link>.
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

      {/* «Принять все» — первой и крупнее: на неё смотрят сначала. Отказ
          остаётся обычной кнопкой той же высоты с читаемым текстом —
          согласие должно быть добровольным, прятать отказ нельзя. */}
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.accept}
          onClick={() => choose("all")}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m5 12.5 4.5 4.5L19 7.5" />
          </svg>
          Принять все
        </button>
        <button
          type="button"
          className={styles.necessary}
          onClick={() => choose("necessary")}
        >
          Только необходимые
        </button>
      </div>
    </div>
  );

  if (!isBlocking) {
    return panel;
  }

  return (
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        if (canDismiss && event.target === event.currentTarget) {
          setIsSettingsOpen(false);
        }
      }}
    >
      {panel}
    </div>
  );
}
