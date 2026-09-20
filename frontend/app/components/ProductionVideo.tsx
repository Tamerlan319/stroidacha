"use client";

import { useState } from "react";

import { reachGoal } from "../lib/metrika";
import styles from "./ProductionVideo.module.css";

const VIDEO_ID = "3ff29be0122297a48183d25af9256489";
const VIDEO_PAGE_URL = `https://rutube.ru/video/${VIDEO_ID}/`;

// Видео с производства в Чухломе. Плеер Rutube грузится только по нажатию:
// до этого страница не обращается к чужому сайту и не отдаёт ему данные
// посетителя — как карты Яндекса (YandexMapConsent.tsx). Заодно страница
// не тянет тяжёлый плеер тем, кто смотреть не собирался.
export default function ProductionVideo() {
  const [isPlayerShown, setIsPlayerShown] = useState(false);

  return (
    <section className={`container section ${styles.section}`}>
      <div className="sectionHeader">
        <p className="eyebrow">Видео</p>
        <h2>Как устроено наше производство</h2>
        <p>
          Цех в Чухломе Костромской области: как отбираем лес, пилим и сушим
          брус, из которого потом собираем дома и бани.
        </p>
      </div>

      <div className={styles.frame}>
        {isPlayerShown ? (
          <iframe
            src={`https://rutube.ru/play/embed/${VIDEO_ID}/`}
            title="Производство Брусодела в Чухломе"
            allow="clipboard-write; autoplay; fullscreen"
            allowFullScreen
          />
        ) : (
          <button
            type="button"
            className={styles.cover}
            onClick={() => {
              setIsPlayerShown(true);
              reachGoal("production_video_play");
            }}
          >
            <span className={styles.play} aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="M8 5.5v13l11-6.5-11-6.5Z" />
              </svg>
            </span>
            <span className={styles.coverText}>
              <strong>Смотреть видео с производства</strong>
              <small>
                Откроется плеер Rutube — он может собирать данные о просмотре
              </small>
            </span>
          </button>
        )}
      </div>

      <p className={styles.fallback}>
        Не открывается плеер?{" "}
        <a href={VIDEO_PAGE_URL} target="_blank" rel="noopener noreferrer">
          Посмотреть на Rutube
        </a>
      </p>
    </section>
  );
}
