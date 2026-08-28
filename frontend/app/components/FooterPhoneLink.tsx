"use client";

import { reachGoal } from "../lib/metrika";
import { SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";

// Отдельный клиентский компонент, а не просто <a onClick=...> прямо в
// SiteFooter — SiteFooter асинхронный серверный компонент (грузит
// landingPages через fetch), обработчики событий туда передать нельзя.
export default function FooterPhoneLink() {
  return (
    <a
      href={`tel:${SITE_PHONE_HREF}`}
      onClick={() => reachGoal("phone_click", { location: "footer" })}
    >
      {SITE_PHONE}
    </a>
  );
}
