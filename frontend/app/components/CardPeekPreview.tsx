"use client";

import Image from "next/image";
import { createPortal } from "react-dom";

import type { CardPeek } from "../lib/useCardPeek";
import styles from "./CardPeekPreview.module.css";

type CardPeekPreviewProps = {
  peek: CardPeek | null;
};

// Окно предпросмотра по долгому нажатию на карточку (lib/useCardPeek.ts).
// Не интерактивное — pointer-events: none: отпускание пальца или кнопки мыши
// должно дойти до страницы под окном и закрыть его. Щипок вторым пальцем
// ловит сам useCardPeek (слушатели на window) и двигает слой zoomLayer.
export default function CardPeekPreview({ peek }: CardPeekPreviewProps) {
  if (!peek || typeof document === "undefined") return null;

  return createPortal(
    <div className={styles.overlay} aria-hidden="true">
      <figure className={styles.frame}>
        <div
          className={`${styles.imageBox} ${peek.isPlan ? styles.imageBoxPlan : ""}`}
        >
          <div
            data-card-peek-zoom=""
            className={styles.zoomLayer}
            style={
              peek.placeholderSrc
                ? { backgroundImage: `url("${peek.placeholderSrc}")` }
                : undefined
            }
          >
            <Image
              src={peek.src}
              alt={peek.alt}
              fill
              sizes="(max-width: 700px) 92vw, 960px"
              draggable={false}
              style={{ objectFit: "contain" }}
            />
          </div>
        </div>
        <figcaption>{peek.caption}</figcaption>
      </figure>
    </div>,
    document.body,
  );
}
