"use client";

import Script from "next/script";
import { useSyncExternalStore } from "react";

import {
  getCookieConsentSnapshot,
  subscribeToCookieConsent,
} from "./CookieBanner";
import { isInsideMetrikaFrame } from "../lib/metrika";
import { YANDEX_METRIKA_ID as METRIKA_ID } from "../lib/site";

// Метрика включается сразу при входе на сайт, без предварительного согласия
// (баннер — уведомление с кнопкой «Отказаться»), и не грузится только у тех,
// кто отказался от аналитики. Во фрейме интерфейса Метрики — всегда, см.
// lib/metrika.ts.
function getMetrikaEnabledSnapshot(): boolean {
  return getCookieConsentSnapshot() !== "essential" || isInsideMetrikaFrame();
}

// false, а не "включено по умолчанию": на сервере выбор посетителя неизвестен,
// и если отрендерить тег уже при гидратации, отказавшемуся посетителю tag.js
// успеет загрузиться раньше, чем клиент прочитает его отказ.
function getServerMetrikaEnabledSnapshot(): boolean {
  return false;
}

export default function YandexMetrika() {
  const enabled = useSyncExternalStore(
    subscribeToCookieConsent,
    getMetrikaEnabledSnapshot,
    getServerMetrikaEnabledSnapshot
  );

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";

  const isLocalSite =
    siteUrl.includes("localhost") || siteUrl.includes("127.0.0.1");

  if (!enabled || isLocalSite) {
    return null;
  }

  return (
    <Script id="yandex-metrika" strategy="afterInteractive">
      {`
        (function(m,e,t,r,i,k,a){
          m[i]=m[i]||function(){
            (m[i].a=m[i].a||[]).push(arguments)
          };

          m[i].l=1*new Date();

          for (var j=0; j<document.scripts.length; j++) {
            if (document.scripts[j].src === r) {
              return;
            }
          }

          k=e.createElement(t);
          a=e.getElementsByTagName(t)[0];
          k.async=1;
          k.src=r;
          a.parentNode.insertBefore(k,a);
        })(
          window,
          document,
          "script",
          "https://mc.yandex.ru/metrika/tag.js?id=${METRIKA_ID}",
          "ym"
        );

        ym(${METRIKA_ID}, "init", {
          ssr: true,
          webvisor: true,
          clickmap: true,
          ecommerce: "dataLayer",
          referrer: document.referrer,
          url: location.href,
          accurateTrackBounce: true,
          trackLinks: true
        });
      `}
    </Script>
  );
}
