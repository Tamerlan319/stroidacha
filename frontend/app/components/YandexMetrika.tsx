"use client";

import Script from "next/script";
import { useSyncExternalStore } from "react";

import {
  getCookieConsentSnapshot,
  getServerCookieConsentSnapshot,
  subscribeToCookieConsent,
} from "./CookieBanner";

const METRIKA_ID = 111281451;

export default function YandexMetrika() {
  const consent = useSyncExternalStore(
    subscribeToCookieConsent,
    getCookieConsentSnapshot,
    getServerCookieConsentSnapshot
  );

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";

  const isLocalSite =
    siteUrl.includes("localhost") || siteUrl.includes("127.0.0.1");

  if (consent !== "all" || isLocalSite) {
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