"use client";

import { useState } from "react";

type ContactMapProps = {
  embedUrl: string;
  linkUrl: string;
  title: string;
};

// Карта Яндекса по умолчанию сразу открывает балун с "Организации в доме" /
// "Сообщить об ошибке" — нормальное поведение виджета для геокодированного
// адреса, но на посадочной странице выглядит как визитка со сторонним шумом
// прямо поверх карты. Параметров, которые бы это чисто отключали, у
// map-widget/v1 нет — вместо борьбы с чужим виджетом показываем карту по
// клику, а не сразу при открытии страницы.
export default function ContactMap({ embedUrl, linkUrl, title }: ContactMapProps) {
  const [isRevealed, setIsRevealed] = useState(false);

  if (!embedUrl) {
    return <div className="contactMapPlaceholder">Карта пока не добавлена</div>;
  }

  if (!isRevealed) {
    return (
      <button
        className="contactMapReveal"
        onClick={() => setIsRevealed(true)}
        type="button"
      >
        <span className="contactMapRevealPin" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M12 22s7-7.58 7-12.5A7 7 0 0 0 5 9.5C5 14.42 12 22 12 22Z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinejoin="round"
            />
            <circle cx="12" cy="9.5" r="2.4" stroke="currentColor" strokeWidth="1.6" />
          </svg>
        </span>
        <span>Показать карту</span>
      </button>
    );
  }

  return (
    <>
      <iframe src={embedUrl} title={title} loading="lazy" />
      <a
        className="contactMapExternalLink"
        href={linkUrl}
        rel="noreferrer"
        target="_blank"
      >
        Открыть в Яндекс.Картах →
      </a>
    </>
  );
}
