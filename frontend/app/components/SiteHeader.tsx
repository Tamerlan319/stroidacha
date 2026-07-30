"use client";

import Link from "next/link";
import { useState } from "react";

const menuItems = [
  { title: "Дома", href: "/doma-iz-brusa" },
  { title: "Бани", href: "/bani-iz-brusa" },
  { title: "Портфолио", href: "/portfolio" },
  { title: "Калькулятор", href: "/calculator" },
  { title: "О компании", href: "/proizvodstvo" },
  { title: "Контакты", href: "/kontakty" },
  { title: "Дополнительно", href: "/#" },
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
          <span className="sdLogoMark">⌂</span>
          <span className="sdLogoText">
            <strong>Брусотека</strong>
            <small>строим дома из бруса</small>
          </span>
        </Link>

        <nav className="sdDesktopNav" aria-label="Основное меню">
          {menuItems.map((item) => (
            <Link href={item.href} key={item.href}>
              {item.title}
            </Link>
          ))}
        </nav>

        <div className="sdHeaderContacts">
          <a className="sdPhone" href="tel:+79676801812">
            +7 967 680-18-12
          </a>
          <small>Ежедневно с 9:00 до 20:00</small>
        </div>

        <Link className="sdHeaderCta" href="/#lead-form">
          Заказать звонок
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

            <a href="tel:+79676801812" onClick={closeMenu}>
              +7 967 680-18-12
            </a>

            <Link className="sdMobileCta" href="/#lead-form" onClick={closeMenu}>
              Заказать звонок
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}
