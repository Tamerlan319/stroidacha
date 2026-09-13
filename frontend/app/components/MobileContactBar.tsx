"use client";

import Image from "next/image";

import { getWhatsAppLink } from "../lib/legalConfig";
import { reachGoal } from "../lib/metrika";
import { SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";
import LeadFormButton from "./LeadFormButton";
import styles from "./MobileContactBar.module.css";
import { useSocialLinks } from "./SocialLinksProvider";

// Нижняя панель связи на телефоне и планшете. В шапке кнопка «Позвонить» и
// мессенджеры спрятаны уже с 1180px (SiteHeaderCallButton.module.css), и
// человек с рекламы — а это почти всегда смартфон — видел телефон только
// внутри меню-бургера. Цели те же, что у кнопок в шапке: phone_click и
// messenger_click, заявка — через обычную форму (lead_submit).
export default function MobileContactBar() {
  const links = useSocialLinks();
  const whatsappUrl =
    links.find((link) => link.platform === "whatsapp")?.url ||
    getWhatsAppLink();

  return (
    <>
      {/* Место под панелью в конце страницы, чтобы она не закрывала футер. */}
      <div className={styles.spacer} aria-hidden="true" />

      <nav className={styles.bar} aria-label="Связаться с нами">
        <a
          className={styles.action}
          href={`tel:${SITE_PHONE_HREF}`}
          aria-label={`Позвонить по номеру ${SITE_PHONE}`}
          onClick={() => reachGoal("phone_click", { location: "mobile_bar" })}
        >
          <svg aria-hidden="true" viewBox="0 0 24 24">
            <path d="M7.2 3.5 10 7.1 8.5 9.4c1.4 2.7 3.4 4.7 6.1 6.1l2.3-1.5 3.6 2.8-.8 2.7c-.2.7-.9 1.1-1.6 1-7.7-1-13.6-6.9-14.6-14.6-.1-.7.3-1.4 1-1.6l2.7-.8Z" />
          </svg>
          <span>Позвонить</span>
        </a>

        <a
          className={styles.action}
          href={whatsappUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() =>
            reachGoal("messenger_click", {
              platform: "whatsapp",
              location: "mobile_bar",
            })
          }
        >
          <Image
            alt=""
            aria-hidden="true"
            className={styles.appIcon}
            height={22}
            src="/social/whatsapp.svg"
            width={22}
          />
          <span>WhatsApp</span>
        </a>

        <LeadFormButton
          className={`${styles.action} ${styles.primary}`}
          source="contact_form"
          title="Бесплатный расчёт"
        >
          Рассчитать
        </LeadFormButton>
      </nav>
    </>
  );
}
