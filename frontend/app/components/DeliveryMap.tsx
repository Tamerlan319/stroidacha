"use client";

import { useEffect, useRef, useState } from "react";

import { useCookieConsent } from "../lib/cookieConsent";
import YandexMapConsent from "./YandexMapConsent";

type DeliveryMapProps = {
  src: string;
  title: string;
  className?: string;
};

// Виджет Яндекс Карт подключается, только когда до блока докрутили. Одного
// loading="lazy" у iframe мало: на медленной сети браузер начинает грузить его
// за несколько экранов, и на 3G главная сразу тянула скрипт, стили, шрифты и
// десятки плиток карты (несколько МБ), хотя карта стоит в самом низу.
//
// Виджет ставит cookie Яндекса, поэтому без согласия на cookie вместо него
// заглушка: карта загрузится по нажатию.
export default function DeliveryMap({ src, title, className }: DeliveryMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isNearViewport, setIsNearViewport] = useState(false);
  const [shownOnRequest, setShownOnRequest] = useState(false);
  const consent = useCookieConsent();
  const isAllowed = consent === "all" || shownOnRequest;

  useEffect(() => {
    const container = containerRef.current;
    if (!container || isNearViewport) return;

    if (typeof IntersectionObserver === "undefined") {
      const timer = setTimeout(() => setIsNearViewport(true), 0);
      return () => clearTimeout(timer);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setIsNearViewport(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px 0px" },
    );
    observer.observe(container);
    return () => observer.disconnect();
  }, [isNearViewport]);

  return (
    <div ref={containerRef} className={className}>
      {!isAllowed ? (
        <YandexMapConsent onShow={() => setShownOnRequest(true)} />
      ) : (
        isNearViewport && (
          <iframe
            src={src}
            title={title}
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        )
      )}
    </div>
  );
}
