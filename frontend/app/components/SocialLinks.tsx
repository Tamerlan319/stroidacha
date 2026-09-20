"use client";

import Image from "next/image";

import { useSocialLinks } from "./SocialLinksProvider";

const PLATFORM_META: Record<string, { title: string; iconSrc: string }> = {
  vk: { title: "ВКонтакте", iconSrc: "/social/vk.svg" },
  max: { title: "MAX", iconSrc: "/social/max.svg" },
  whatsapp: { title: "WhatsApp", iconSrc: "/social/whatsapp.svg" },
  telegram: { title: "Telegram", iconSrc: "/social/telegram.svg" },
};

// Резервный список — только на случай, если запрос к API не удался при
// самой первой загрузке layout.tsx. Реальные ссылки редактируются в Django
// Admin (модель SocialLink), не здесь.
const FALLBACK_LINKS = [
  { platform: "vk", url: "https://vk.com/" },
  { platform: "max", url: "https://max.ru/" },
  { platform: "whatsapp", url: "https://api.whatsapp.com/send?phone=79676801812" },
  { platform: "telegram", url: "https://t.me/brusodel_bot" },
];

type SocialLinksProps = {
  className?: string;
  // Место на сайте для цели «Клик по мессенджеру». Саму цель отправляет общий
  // обработчик ссылок в YandexMetrika.tsx.
  location?: string;
  // Площадки, которые здесь не показываем. В шапке оставлены только
  // WhatsApp и Telegram — туда пишут клиенты, а ВКонтакте и MAX остаются
  // в подвале и в форме заявки.
  exclude?: string[];
};

export default function SocialLinks({
  className = "",
  location,
  exclude,
}: SocialLinksProps) {
  const contextLinks = useSocialLinks();
  const allLinks = contextLinks.length > 0 ? contextLinks : FALLBACK_LINKS;
  const links = exclude
    ? allLinks.filter((item) => !exclude.includes(item.platform))
    : allLinks;

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
