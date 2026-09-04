"use client";

import Image from "next/image";

import { reachGoal } from "../lib/metrika";
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
};

export default function SocialLinks({ className = "" }: SocialLinksProps) {
  const contextLinks = useSocialLinks();
  const links = contextLinks.length > 0 ? contextLinks : FALLBACK_LINKS;

  return (
    <div
      className={`sdSocialLinks ${className}`}
      aria-label="Связаться в мессенджерах"
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
            onClick={() => reachGoal("messenger_click", { platform: item.platform })}
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
