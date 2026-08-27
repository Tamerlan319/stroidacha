"use client";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

import LeadForm from "./LeadForm";
import styles from "./LeadFormModal.module.css";

type LeadFormModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  source?: string;
  projectSlug?: string;
};

// Всплывающее окно с формой заявки поверх любой страницы. Логика
// блокировки скролла и фокуса повторяет ImageLightbox.tsx — единый
// проверенный паттерн модалки для всего сайта.
export default function LeadFormModal({
  open,
  onClose,
  title,
  source,
  projectSlug,
}: LeadFormModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    const body = document.body;
    const html = document.documentElement;
    const scrollY = window.scrollY;
    const previouslyFocusedElement =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;

    const previousBodyStyles = {
      position: body.style.position,
      top: body.style.top,
      right: body.style.right,
      bottom: body.style.bottom,
      left: body.style.left,
      width: body.style.width,
      overflow: body.style.overflow,
    };
    const previousHtmlOverflow = html.style.overflow;

    body.style.position = "fixed";
    body.style.top = `-${scrollY}px`;
    body.style.right = "0";
    body.style.bottom = "0";
    body.style.left = "0";
    body.style.width = "100%";
    body.style.overflow = "hidden";
    html.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    const focusFrame = window.requestAnimationFrame(() => {
      closeButtonRef.current?.focus({ preventScroll: true });
    });

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      window.cancelAnimationFrame(focusFrame);

      body.style.position = previousBodyStyles.position;
      body.style.top = previousBodyStyles.top;
      body.style.right = previousBodyStyles.right;
      body.style.bottom = previousBodyStyles.bottom;
      body.style.left = previousBodyStyles.left;
      body.style.width = previousBodyStyles.width;
      body.style.overflow = previousBodyStyles.overflow;
      html.style.overflow = previousHtmlOverflow;
      window.scrollTo(0, scrollY);
      previouslyFocusedElement?.focus({ preventScroll: true });
    };
  }, [open, onClose]);

  if (!open || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-label={title || "Оставить заявку"}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className={styles.panel}>
        <button
          ref={closeButtonRef}
          type="button"
          className={styles.closeButton}
          aria-label="Закрыть форму заявки"
          onClick={onClose}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6 18 18M18 6 6 18" />
          </svg>
        </button>

        <LeadForm title={title} source={source} projectSlug={projectSlug} />
      </div>
    </div>,
    document.body
  );
}
