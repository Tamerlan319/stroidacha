"use client";

import Script from "next/script";
import { useEffect, useState } from "react";

import {
  COOKIE_CONSENT_EVENT,
  COOKIE_CONSENT_STORAGE_KEY,
} from "./CookieBanner";

export default function YandexMetrika() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";
  const [isAllowed, setIsAllowed] = useState(false);

  useEffect(() => {
    function syncConsent() {
      setIsAllowed(
        window.localStorage.getItem(COOKIE_CONSENT_STORAGE_KEY) === "all"
      );
    }

    syncConsent();
    window.addEventListener(COOKIE_CONSENT_EVENT, syncConsent);

    return () => {
      window.removeEventListener(COOKIE_CONSENT_EVENT, syncConsent);
    };
  }, []);

  if (
    !isAllowed ||
    siteUrl.includes("localhost") ||
    siteUrl.includes("127.0.0.1")
  ) {
    return null;
  }

  return (
    <Script id="yandex-metrika" strategy="afterInteractive">
      {`
        (function(m,e,t,r,i,k,a){
          m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
          m[i].l=1*new Date();
          for (var j=0; j<document.scripts.length; j++) {
            if (document.scripts[j].src === r) return;
          }
          k=e.createElement(t);
          a=e.getElementsByTagName(t)[0];
          k.async=1;
          k.src=r;
          a.parentNode.insertBefore(k,a);
        })(window, document, "script",
          "https://mc.yandex.ru/metrika/tag.js?id=111150898", "ym");
        ym(111150898, "init", {
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
