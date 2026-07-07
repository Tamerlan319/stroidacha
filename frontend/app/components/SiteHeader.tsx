"use client";

import Link from "next/link";
import { useState } from "react";

const menuItems = [
  { title: "Дома", href: "/doma-iz-brusa" },
  { title: "Бани", href: "/bani-iz-brusa" },
  { title: "Гаражи", href: "/garazhi-pod-klyuch" },
  { title: "Доставка", href: "/dostavka-po-rossii" },
  { title: "Производство", href: "/proizvodstvo" },
];

export default function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);

  function closeMenu() {
    setIsOpen(false);
  }

  return (
    <header className="sdHeader">
      <div className="container sdHeaderInner">
        <Link className="sdLogo" href="/" onClick={closeMenu}>
          <span className="sdLogoMark">СД</span>
          <span className="sdLogoText">
            <strong>СтройДача</strong>
            <small>дома, бани и гаражи из бруса</small>
          </span>
        </Link>

        <nav className="sdDesktopNav" aria-label="Основное меню">
          {menuItems.map((item) => (
            <Link href={item.href} key={item.href}>
              {item.title}
            </Link>
          ))}
        </nav>

        <a className="sdPhone" href="tel:+79999999999">
          +7 999 999-99-99
        </a>

        <Link className="sdHeaderCta" href="/#lead-form">
          Получить расчёт
        </Link>

        <button
          className="sdBurger"
          type="button"
          aria-label={isOpen ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={isOpen}
          onClick={() => setIsOpen((current) => !current)}
        >
          <span className={isOpen ? "active" : ""} />
          <span className={isOpen ? "active" : ""} />
          <span className={isOpen ? "active" : ""} />
        </button>
      </div>

      {isOpen && (
        <nav className="sdMobileMenu" aria-label="Мобильное меню">
          <div className="container sdMobileMenuInner">
            {menuItems.map((item) => (
              <Link href={item.href} key={item.href} onClick={closeMenu}>
                {item.title}
              </Link>
            ))}

            <a href="tel:+79999999999" onClick={closeMenu}>
              +7 999 999-99-99
            </a>

            <Link className="sdMobileCta" href="/#lead-form" onClick={closeMenu}>
              Получить расчёт
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}