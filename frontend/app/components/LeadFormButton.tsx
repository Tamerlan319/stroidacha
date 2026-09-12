"use client";

import { type ReactNode, useCallback, useState } from "react";

import LeadFormModal from "./LeadFormModal";

type LeadFormButtonProps = {
  children: ReactNode;
  source: string;
  title?: string;
  projectSlug?: string;
  className?: string;
  // Куда ведёт ссылка, пока JavaScript не загрузился, — к форме на странице.
  fallbackHref?: string;
};

// Кнопка заявки: открывает форму во всплывающем окне, как «Оставить заявку»
// на главной (HeroLeadCard). Внутри та же LeadForm, поэтому цель «Заявка
// отправлена» (lead_submit) срабатывает при успешной отправке ровно так же,
// как у формы внизу страницы, — цели в Метрике и стратегия Директа не
// меняются. source передаётся тот же, что у формы на этой странице.
//
// Разметка — обычная ссылка на форму: если скрипты ещё не загрузились или
// отключены, кнопка, как раньше, прокручивает к форме внизу страницы.
export default function LeadFormButton({
  children,
  source,
  title,
  projectSlug,
  className,
  fallbackHref = "#lead-form",
}: LeadFormButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const close = useCallback(() => setIsOpen(false), []);

  return (
    <>
      <a
        href={fallbackHref}
        className={className}
        onClick={(event) => {
          event.preventDefault();
          setIsOpen(true);
        }}
      >
        {children}
      </a>

      <LeadFormModal
        open={isOpen}
        onClose={close}
        title={title}
        source={source}
        projectSlug={projectSlug}
      />
    </>
  );
}
