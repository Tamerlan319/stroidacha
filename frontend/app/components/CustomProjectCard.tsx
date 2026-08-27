"use client";

import { useState } from "react";

import LeadFormModal from "./LeadFormModal";
import SiteIcon from "./SiteIcon";
import styles from "./CustomProjectCard.module.css";

// Первая карточка любого каталога проектов — предложение прислать свой
// эскиз/фото и получить расчёт индивидуального проекта. Переиспользует
// глобальные классы .projectCard/.projectImage/.projectBody/.projectFooter,
// поэтому автоматически выглядит как остальные карточки каталога (в том
// числе внутри .homeEditorial на главной). Источник заявки "own_project"
// уже был в backend/leads/models.py, но нигде на сайте не использовался —
// эта карточка наконец задействует его по назначению.
export default function CustomProjectCard() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <article className="projectCard">
        <button
          type="button"
          className={styles.trigger}
          aria-label="Прислать свой проект — открыть форму заявки"
          onClick={() => setIsOpen(true)}
        >
          <div className="projectImage">
            <div className={styles.visual}>
              <SiteIcon name="blueprint" className={styles.ghostIcon} />
              <SiteIcon name="blueprint" className={styles.mainIcon} />
            </div>
            <span className="projectBadge">Индивидуально</span>
          </div>

          <div className="projectBody">
            <h3>Свой проект дома или бани</h3>
            <p>
              Пришлём расчёт по вашему эскизу, фото или желаемой планировке —
              учтём размеры и пожелания.
            </p>

            <div className="projectFooter">
              <strong>Бесплатно</strong>
              <span className={styles.ctaPill}>Отправить эскиз →</span>
            </div>
          </div>
        </button>
      </article>

      <LeadFormModal
        open={isOpen}
        onClose={() => setIsOpen(false)}
        title="Пришлите свой проект"
        source="own_project"
      />
    </>
  );
}
