"use client";

import { useEffect } from "react";

import { captureUtmFromUrl } from "../lib/utm";

// Запоминает utm-метки при входе на сайт, чтобы они дожили до отправки
// заявки (см. lib/utm.ts). Намеренно не внутри YandexMetrika: та у
// отказавшихся от аналитики не рендерится вовсе, а метки нужны самой заявке.
//
// Layout в App Router не перемонтируется при переходах внутри сайта, но это
// и не нужно: метки приходят только с полной загрузкой страницы по клику из
// рекламы, а её этот эффект как раз и ловит.
export default function UtmCapture() {
  useEffect(() => {
    captureUtmFromUrl();
  }, []);

  return null;
}
