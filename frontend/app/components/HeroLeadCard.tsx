"use client";

import { useState } from "react";

import LeadFormModal from "./LeadFormModal";
import SocialLinks from "./SocialLinks";
import { SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";
import styles from "./HeroLeadCard.module.css";

const benefits = [
  "Подберём проект под участок и бюджет",
  "Расчёт бесплатный, без обязательств",
];

// Мини-окно заявки в баннере главной страницы. Карточка — лёгкий тизер,
// клик по кнопке открывает LeadFormModal с полной формой (см. пустую
// 360px-колонку .homeHeroGrid и стили .heroLeadCard в globals.css —
// место под эту карточку в вёрстке уже было предусмотрено).
export default function HeroLeadCard() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={styles.card}>
      <span className={styles.badge}>Бесплатно</span>
      <strong className={styles.title}>Узнайте стоимость вашего дома</strong>

      <ul className={styles.list}>
        {benefits.map((benefit) => (
          <li key={benefit}>
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <path d="m4 10.5 3.8 3.8L16 6" />
            </svg>
            <span>{benefit}</span>
          </li>
        ))}
      </ul>

      <button
        type="button"
        className={`buttonPrimary ${styles.cta}`}
        onClick={() => setIsOpen(true)}
      >
        Оставить заявку
      </button>

      <a className={styles.phone} href={`tel:${SITE_PHONE_HREF}`}>
        Или позвоните: {SITE_PHONE}
      </a>

      <SocialLinks className={styles.social} />

      <LeadFormModal
        open={isOpen}
        onClose={() => setIsOpen(false)}
        title="Бесплатный расчёт стоимости"
        source="home_hero_popup"
      />
    </div>
  );
}
