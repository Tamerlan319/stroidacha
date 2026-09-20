"use client";

import Image from "next/image";

import { SITE_EMAIL } from "../lib/site";
import { useSocialLinks } from "./SocialLinksProvider";

const PLATFORM_META: Record<string, { title: string; iconSrc: string }> = {
  whatsapp: { title: "WhatsApp", iconSrc: "/social/whatsapp.svg" },
  telegram: { title: "Telegram", iconSrc: "/social/telegram.svg" },
  mail: { title: "Написать на почту", iconSrc: "/social/yandex-mail.svg" },
};

// Почта стоит рядом с мессенджерами везде, где они есть, и ведёт в
// веб-интерфейс Яндекс Почты с подставленным адресом (как ссылка в шапке).
// В админке её нет: это не мессенджер, а постоянный адрес компании.
const MAIL_URL = "https://mail.yandex.ru/compose?mailto=";

// Показываем только мессенджеры, где действительно отвечают. Ссылки
// ВКонтакте и MAX могут оставаться в админке (модель SocialLink) — на сайт
// они не попадут, пока платформы нет в этом списке.
const MESSENGER_PLATFORMS = ["whatsapp", "telegram"];

// Резервный список — только на случай, если запрос к API не удался при
// самой первой загрузке layout.tsx. Реальные ссылки редактируются в Django
// Admin (модель SocialLink), не здесь.
const FALLBACK_LINKS = [
  { platform: "whatsapp", url: "https://api.whatsapp.com/send?phone=79676801812" },
  { platform: "telegram", url: "https://t.me/brusodel_bot" },
];

type SocialLinksProps = {
  className?: string;
  // Место на сайте для цели «Клик по мессенджеру». Саму цель отправляет общий
  // обработчик ссылок в YandexMetrika.tsx.
  location?: string;
};

export default function SocialLinks({ className = "", location }: SocialLinksProps) {
  const contextLinks = useSocialLinks();
  const allLinks = contextLinks.length > 0 ? contextLinks : FALLBACK_LINKS;
  const links = [
    ...allLinks.filter((item) => MESSENGER_PLATFORMS.includes(item.platform)),
    { platform: "mail", url: `${MAIL_URL}${SITE_EMAIL}` },
  ];

  return (
    <div
      className={`sdSocialLinks ${className}`}
      aria-label="Связаться в мессенджерах"
      data-goal-location={location}
    >
      {links.map((item) => {
        const meta = PLATFORM_META[item.platform];
        if (!meta) return null;

        return (
          <a
            aria-label={meta.title}
            href={item.url}
            key={item.platform}
            rel="noopener noreferrer"
            target="_blank"
            title={meta.title}
          >
            <Image
              alt=""
              aria-hidden="true"
              className="sdSocialAppIcon"
              height={31}
              src={meta.iconSrc}
              width={31}
            />
          </a>
        );
      })}
    </div>
  );
}
