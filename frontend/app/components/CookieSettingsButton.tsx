"use client";

import { openCookieSettings } from "../lib/cookieConsent";

type CookieSettingsButtonProps = {
  className?: string;
};

// «Настройки cookie» в подвале: снова открывает баннер, чтобы изменить или
// отозвать согласие (152-ФЗ, ст. 9 ч. 2).
export default function CookieSettingsButton({ className }: CookieSettingsButtonProps) {
  return (
    <button type="button" className={className} onClick={openCookieSettings}>
      Настройки cookie
    </button>
  );
}
