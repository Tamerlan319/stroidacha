"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { CATALOG_LINKS, SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";
import BrandMark from "./BrandMark";
import SiteIcon from "./SiteIcon";

const menuItems = [
  { title: "Портфолио", href: "/portfolio" },
  { title: "Калькулятор", href: "/calculator" },
  { title: "О компании", href: "/proizvodstvo" },
  { title: "Контакты", href: "/kontakty" },
];

export default function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const catalogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (
        catalogRef.current &&
        !catalogRef.current.contains(event.target as Node)
      ) {
        setIsCatalogOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsCatalogOpen(false);
        setIsOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  function closeMenu() {
    setIsOpen(false);
    setIsCatalogOpen(false);
  }

  return (
    <header className="sdHeader">
      <div className="container sdHeaderInner">
        <Link className="sdLogo" href="/" onClick={closeMenu}>
          <span className="sdLogoMark">
            <BrandMark />
          </span>
          <span className="sdLogoText">
            <strong>Брусотека</strong>
            <small>строим дома из бруса</small>
          </span>
        </Link>

        <nav className="sdDesktopNav" aria-label="Основное меню">
          <div
            className={`sdNavDropdown ${isCatalogOpen ? "isOpen" : ""}`}
            onMouseEnter={() => setIsCatalogOpen(true)}
            onMouseLeave={() => setIsCatalogOpen(false)}
            ref={catalogRef}
          >
            <button
              aria-expanded={isCatalogOpen}
              className="sdNavDropdownTrigger"
              onClick={() => setIsCatalogOpen((current) => !current)}
              type="button"
            >
              Каталог
              <SiteIcon className="sdNavChevron" name="chevron" />
            </button>

            {isCatalogOpen && (
              <div className="sdNavDropdownMenu">
                {CATALOG_LINKS.map((item) => (
                  <Link
                    href={item.href}
                    key={item.href}
                    onClick={closeMenu}
                  >
                    <span className="sdNavDropdownIcon">
                      <SiteIcon name={item.icon} />
                    </span>
                    <span>
                      <strong>{item.title}</strong>
                      <small>{item.description}</small>
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {menuItems.map((item) => (
            <Link href={item.href} key={item.href} onClick={closeMenu}>
              {item.title}
            </Link>
          ))}
        </nav>

        <div className="sdHeaderContacts">
          <a className="sdPhone" href={`tel:${SITE_PHONE_HREF}`}>
            {SITE_PHONE}
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
            <button
              aria-expanded={isCatalogOpen}
              className="sdMobileCatalogToggle"
              onClick={() => setIsCatalogOpen((current) => !current)}
              type="button"
            >
              Каталог
              <SiteIcon className="sdNavChevron" name="chevron" />
            </button>

            {isCatalogOpen && (
              <div className="sdMobileCatalogLinks">
                {CATALOG_LINKS.map((item) => (
                  <Link href={item.href} key={item.href} onClick={closeMenu}>
                    <SiteIcon name={item.icon} />
                    {item.title}
                  </Link>
                ))}
              </div>
            )}

            {menuItems.map((item) => (
              <Link href={item.href} key={item.href} onClick={closeMenu}>
                {item.title}
              </Link>
            ))}

            <a href={`tel:${SITE_PHONE_HREF}`} onClick={closeMenu}>
              {SITE_PHONE}
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
