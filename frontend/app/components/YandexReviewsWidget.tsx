"use client";

import { useState } from "react";

import styles from "./YandexReviewsWidget.module.css";

// ID организации "СтройДача" на Яндекс Картах (business.yandex.ru — та же
// организация, что и у офисов на /kontakty). Отзывы и рейтинг в виджете
// подтягиваются с Яндекса напрямую и обновляются раз в ~72 часа — эта
// цифра не связана с локальными отзывами из Django Admin (content.Review)
// и специально не смешивается с ними: это два независимых источника.
const YANDEX_ORGANIZATION_ID = "109967944436";
const YANDEX_ORGANIZATION_URL = `https://yandex.ru/maps/org/stroydacha/${YANDEX_ORGANIZATION_ID}/`;

export default function YandexReviewsWidget() {
  const [isLoaded, setIsLoaded] = useState(false);

  return (
    <div className={styles.wrapper}>
      {isLoaded ? (
        <div className={styles.frameBox}>
          <iframe
            className={styles.frame}
            src={`https://yandex.ru/maps-reviews-widget/${YANDEX_ORGANIZATION_ID}?comments`}
            title="Отзывы на Яндекс Картах"
            loading="lazy"
          />
          {/* Атрибуция — условие использования виджета от Яндекса,
              убирать нельзя. */}
          <a
            className={styles.attribution}
            href={YANDEX_ORGANIZATION_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            СтройДача — Яндекс Карты
          </a>
        </div>
      ) : (
        <button
          type="button"
          className={styles.placeholder}
          onClick={() => setIsLoaded(true)}
        >
          <span className={styles.placeholderIcon} aria-hidden="true">
            ★
          </span>
          <strong>Показать отзывы с Яндекс Карт</strong>
          <span>Загрузится виджет с сайта Яндекса</span>
        </button>
      )}
    </div>
  );
}
