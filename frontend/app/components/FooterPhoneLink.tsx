import { SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";

// Телефон в подвале. Цель «Клик по телефону» отправляет общий обработчик
// ссылок tel: в YandexMetrika.tsx, место клика — data-goal-location.
export default function FooterPhoneLink() {
  return (
    <a href={`tel:${SITE_PHONE_HREF}`} data-goal-location="footer">
      {SITE_PHONE}
    </a>
  );
}
