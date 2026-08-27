import Image from "next/image";

const socialLinks = [
  {
    title: "ВКонтакте",
    href: process.env.NEXT_PUBLIC_VK_URL || "https://vk.com/",
    iconSrc: "/social/vk.svg",
  },
  {
    title: "MAX",
    href: process.env.NEXT_PUBLIC_MAX_URL || "https://max.ru/",
    iconSrc: "/social/max.svg",
  },
  {
    title: "WhatsApp",
    href: "https://api.whatsapp.com/send?phone=79676801812",
    iconSrc: "/social/whatsapp.svg",
  },
  {
    title: "Telegram",
    href: process.env.NEXT_PUBLIC_TELEGRAM_URL || "https://t.me/+79676801812",
    iconSrc: "/social/telegram.svg",
  },
] as const;

type SocialLinksProps = {
  className?: string;
};

// Общий ряд иконок мессенджеров/соцсетей — используется в шапке сайта и в
// LeadForm (вместо одиночной кнопки WhatsApp). Единый источник данных, чтобы
// ссылки не расходились между местами использования.
export default function SocialLinks({ className = "" }: SocialLinksProps) {
  return (
    <div
      className={`sdSocialLinks ${className}`}
      aria-label="Связаться в мессенджерах"
    >
      {socialLinks.map((item) => (
        <a
          aria-label={item.title}
          href={item.href}
          key={item.title}
          rel="noopener noreferrer"
          target="_blank"
          title={item.title}
        >
          <Image
            alt=""
            aria-hidden="true"
            className="sdSocialAppIcon"
            height={31}
            src={item.iconSrc}
            width={31}
          />
        </a>
      ))}
    </div>
  );
}
