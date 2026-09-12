"use client";

import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";

import { legalConfig } from "../lib/legalConfig";
import styles from "./LeadSuccessDialog.module.css";

type LeadSuccessDialogProps = {
  open: boolean;
  onClose: () => void;
};

// Подтверждение после успешной отправки заявки — одно на все формы:
// LeadForm (в том числе внутри LeadFormModal) и мини-форму в шапке.
export default function LeadSuccessDialog({
  open,
  onClose,
}: LeadSuccessDialogProps) {
  const titleId = useId();
  const textId = useId();
  const okButtonRef = useRef<HTMLButtonElement>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) return;

    const html = document.documentElement;
    const previouslyFocusedElement =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    // Если заявка ушла из всплывающей формы, прокрутку страницы уже держит
    // LeadFormModal (body position: fixed). Второй раз её не трогаем, иначе
    // при закрытии вернули бы не те стили.
    const lockScroll = document.body.style.position !== "fixed";
    const previousOverflow = html.style.overflow;

    if (lockScroll) html.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        // В фазе захвата и без всплытия — раньше, чем Esc поймает
        // LeadFormModal: закрываем это окно, а форму закроет onClose.
        event.preventDefault();
        event.stopPropagation();
        onCloseRef.current();
        return;
      }

      if (event.key === "Tab") {
        // Единственная кнопка — фокус не уходит на страницу под окном.
        event.preventDefault();
        okButtonRef.current?.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown, true);
    const focusFrame = window.requestAnimationFrame(() => {
      okButtonRef.current?.focus({ preventScroll: true });
    });

    return () => {
      document.removeEventListener("keydown", handleKeyDown, true);
      window.cancelAnimationFrame(focusFrame);
      if (lockScroll) html.style.overflow = previousOverflow;
      previouslyFocusedElement?.focus({ preventScroll: true });
    };
  }, [open]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className={styles.dialog}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={textId}
      >
        <span className={styles.icon} aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="m5 12.5 4.5 4.5L19 7.5" />
          </svg>
        </span>

        <h2 id={titleId}>Заявка отправлена</h2>
        <p id={textId}>
          Менеджер перезвонит вам в рабочее время —{" "}
          {legalConfig.workHours.toLowerCase()}.
        </p>

        <button
          ref={okButtonRef}
          type="button"
          className={styles.okButton}
          onClick={onClose}
        >
          Хорошо
        </button>
      </div>
    </div>,
    document.body,
  );
}
