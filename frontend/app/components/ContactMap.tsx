"use client";

import { useState } from "react";

import { useCookieConsent } from "../lib/cookieConsent";
import YandexMapConsent from "./YandexMapConsent";

type ContactMapProps = {
  embedUrl: string;
  linkUrl: string;
  title: string;
};

// Карта Яндекса при открытии сама показывает балун "Организации в доме" /
// "Сообщить об ошибке" — это поведение встроенного виджета Яндекса для
// геокодированного адреса, средствами iframe его не убрать (кросс-доменная
// страница, до её внутренней вёрстки нет доступа), а платный вариант без
// этого (Static Maps API) требует отдельного API-ключа и биллинга.
//
// Виджет ставит cookie Яндекса, поэтому без согласия на cookie вместо карты
// заглушка: карта загрузится по нажатию. Ссылка на Яндекс Карты есть всегда.
export default function ContactMap({ embedUrl, linkUrl, title }: ContactMapProps) {
  const consent = useCookieConsent();
  const [shownOnRequest, setShownOnRequest] = useState(false);

  if (!embedUrl) {
    return <div className="contactMapPlaceholder">Карта пока не добавлена</div>;
  }

  return (
    <>
      {consent === "all" || shownOnRequest ? (
        <iframe src={embedUrl} title={title} loading="lazy" />
      ) : (
        <YandexMapConsent onShow={() => setShownOnRequest(true)} />
      )}
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
