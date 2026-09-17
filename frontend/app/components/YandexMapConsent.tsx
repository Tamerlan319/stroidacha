"use client";

import styles from "./YandexMapConsent.module.css";

type YandexMapConsentProps = {
  onShow: () => void;
  label?: string;
};

// Заглушка вместо карты Яндекса, пока посетитель не согласился на cookie:
// виджет Яндекса при загрузке ставит свои cookie, поэтому карта грузится
// только после «Принять все» в баннере или по нажатию на эту кнопку.
export default function YandexMapConsent({
  onShow,
  label = "Показать карту",
}: YandexMapConsentProps) {
  return (
    <button type="button" className={styles.placeholder} onClick={onShow}>
      <span className={styles.icon} aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z" />
          <circle cx="12" cy="9.5" r="2.5" />
        </svg>
      </span>
      <strong>{label}</strong>
      <span>Карта загрузится с сайта Яндекса, он может установить свои cookie</span>
    </button>
  );
}
