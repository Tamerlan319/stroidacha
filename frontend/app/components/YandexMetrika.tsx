"use client";

import Script from "next/script";

import { YANDEX_METRIKA_ID as METRIKA_ID } from "../lib/site";

// Метрика грузится у всех посетителей сразу: cookie-баннера и согласия на
// сайте нет по решению владельца, своё согласие он планирует сделать позже.
// Если оно вернётся — карта кликов, аналитика форм и Вебвизор открывают сайт
// во фрейме интерфейса Метрики, где хранилище отделено браузером от обычного
// визита и согласия нет никогда. Там счётчик должен грузиться без него,
// иначе Метрика пишет «Не установлен код счётчика» (так уже было и
// исправлялось — см. историю этого файла и lib/metrika.ts).
export default function YandexMetrika() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";

  const isLocalSite =
    siteUrl.includes("localhost") || siteUrl.includes("127.0.0.1");

  if (isLocalSite) {
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
