"use client";

import { usePathname } from "next/navigation";
import Script from "next/script";
import { useEffect, useRef, useSyncExternalStore } from "react";

import { useCookieConsent } from "../lib/cookieConsent";
import {
  getServerMetrikaFrameSnapshot,
  isInsideMetrikaFrame,
  messengerPlatform,
  reachGoal,
  subscribeToMetrikaFrame,
  trackPageview,
} from "../lib/metrika";
import { YANDEX_METRIKA_ID as METRIKA_ID } from "../lib/site";

function subscribeToNothing() {
  return () => undefined;
}

// Метрика грузится сразу при входе на сайт — об этом сообщает уведомление в
// углу (CookieNotice.tsx) и политики. Так решил владелец: окно с выбором до
// загрузки счётчика оставляло Метрику без большинства визитов из рекламы.
// Не грузится только у тех, кто раньше нажал «Только необходимые» в прежнем
// окне выбора (CookieBanner.tsx, отключено). Вернуть загрузку только после
// согласия — условие ниже на consent === "all" и окно выбора в layout.tsx.
//
// Фрейм интерфейса Метрики (карта кликов, аналитика форм, Вебвизор): там
// страницу смотрит владелец счётчика, хранилище фрейма браузер держит
// отдельно, а без счётчика Метрика пишет «Не установлен код счётчика» (см.
// lib/metrika.ts).
export default function YandexMetrika() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";
  const pathname = usePathname();
  const consent = useCookieConsent();
  // Только на клиенте, после чтения выбора: скрипт, отрисованный на сервере,
  // Next запустил бы ещё до гидратации — в том числе у отказавшихся.
  const isClient = useSyncExternalStore(
    subscribeToNothing,
    () => true,
    () => false
  );
  const insideMetrikaFrame = useSyncExternalStore(
    subscribeToMetrikaFrame,
    isInsideMetrikaFrame,
    getServerMetrikaFrameSnapshot
  );
  const lastUrlRef = useRef<string | null>(null);

  // Переходы внутри сайта — отдельные просмотры в Метрике (см. trackPageview).
  // Фильтры каталога меняют только ?query, а не путь, и просмотрами не
  // считаются — иначе каждый клик по фильтру выглядел бы новой страницей.
  useEffect(() => {
    const url = window.location.href;
    const previousUrl = lastUrlRef.current;
    lastUrlRef.current = url;

    // Первый просмотр отправляет сам счётчик при init.
    if (previousUrl === null || previousUrl === url) return;

    // Заголовок новой страницы Next проставляет чуть позже смены адреса.
    window.setTimeout(() => {
      trackPageview(url, previousUrl, document.title);
    }, 0);
  }, [pathname]);

  // Цели «Клик по телефону» и «Клик по мессенджеру» — одним обработчиком на
  // весь сайт: любая ссылка tel: или ссылка мессенджера, где бы она ни стояла
  // (шапка, подвал, контакты, калькулятор, тексты из админки). Раньше цель
  // висела на каждой кнопке отдельно, и часть мест её не отправляла —
  // например, страница контактов. Место клика — data-goal-location у ссылки
  // или ближайшего родителя, иначе адрес страницы.
  useEffect(() => {
    function handleClick(event: MouseEvent) {
      const target = event.target;
      const link = target instanceof Element ? target.closest("a[href]") : null;
      if (!link) return;

      const href = link.getAttribute("href") || "";
      const location =
        link.closest("[data-goal-location]")?.getAttribute("data-goal-location") ||
        window.location.pathname;

      if (href.startsWith("tel:")) {
        reachGoal("phone_click", { location });
        return;
      }

      if (href.startsWith("mailto:")) {
        reachGoal("email_click", { location });
        return;
      }

      const platform = messengerPlatform(href);
      if (platform) {
        reachGoal("messenger_click", { platform, location });
      }
    }

    // Фаза перехвата: цель уходит раньше, чем меню успеет закрыться, а
    // ссылка — открыть звонилку или мессенджер.
    document.addEventListener("click", handleClick, true);
    return () => document.removeEventListener("click", handleClick, true);
  }, []);

  const isLocalSite =
    siteUrl.includes("localhost") || siteUrl.includes("127.0.0.1");

  if (
    !isClient ||
    isLocalSite ||
    (consent === "necessary" && !insideMetrikaFrame)
  ) {
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
