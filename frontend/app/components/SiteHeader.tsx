"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { CATALOG_LINKS, SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";
import BrandMark from "./BrandMark";
import SiteIcon from "./SiteIcon";
import SocialLinks from "./SocialLinks";
import headerStyles from "./SiteHeaderCallButton.module.css";

type HeaderLink = {
  title: string;
  href: string;
};

type LandingPageListItem = {
  title: string;
  slug: string;
  page_type: string;
  sort_order: number;
};

const companyLinks: HeaderLink[] = [
  { title: "О директоре", href: "/o-direktore" },
  { title: "Выписка из ЕГРЮЛ", href: "/vypiska-iz-egryul" },
  { title: "Производство", href: "/proizvodstvo" },
  { title: "Доставка", href: "/dostavka" },
  { title: "Маткапитал", href: "/materinskij-kapital" },
  { title: "Ипотека", href: "/ipoteka" },
];

export default function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<
    "catalog" | "company" | "guide" | null
  >(null);
  const [guideLinks, setGuideLinks] = useState<HeaderLink[]>([
    { title: "Все статьи", href: "/spravochnik" },
  ]);
  const headerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node;
      if (!headerRef.current?.contains(target)) {
        setOpenDropdown(null);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpenDropdown(null);
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

  useEffect(() => {
    let isCancelled = false;

    async function loadGuideLinks() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/landing-pages/`
        );

        if (!response.ok) {
          return;
        }

        const pages = (await response.json()) as LandingPageListItem[];
        const articles = pages
          .filter((page) => page.page_type === "guide")
          .sort((a, b) => a.sort_order - b.sort_order)
          .map((page) => ({
            title: page.title,
            href: `/${page.slug}`,
          }));

        if (!isCancelled) {
          setGuideLinks([
            { title: "Все статьи", href: "/spravochnik" },
            ...articles,
          ]);
        }
      } catch {
        // Справочник остаётся доступен при временной недоступности API.
      }
    }

    loadGuideLinks();

    return () => {
      isCancelled = true;
    };
  }, []);

  useEffect(() => {
    document.body.classList.toggle("sdMobileMenuOpen", isOpen);

    return () => {
      document.body.classList.remove("sdMobileMenuOpen");
    };
  }, [isOpen]);

  function closeMenu() {
    setIsOpen(false);
    setOpenDropdown(null);
  }

  function toggleMobileMenu() {
    setIsOpen((current) => {
      if (current) {
        setOpenDropdown(null);
      }

      return !current;
    });
  }

  return (
    <header className="sdHeader" ref={headerRef}>
      <div className="sdHeaderMain">
        <div className="container sdHeaderInner">
          <Link className="sdLogo" href="/" onClick={closeMenu}>
            <span className="sdLogoMark">
              <BrandMark />
            </span>
            <span className="sdLogoText">
              <strong>Брусодел</strong>
              <small>строим дома из бруса</small>
            </span>
          </Link>

          <p className="sdHeaderPromise">
            Дома и бани из бруса
            <br />
            от производителя
          </p>

          <SocialLinks className="sdHeaderSocials" />

          <div className={headerStyles.contactActions}>
            <div className="sdHeaderContacts">
              <a className="sdPhone" href={`tel:${SITE_PHONE_HREF}`}>
                {SITE_PHONE}
              </a>
              <small>Ежедневно с 9:00 до 20:00</small>
            </div>

            <a
              className={headerStyles.callButton}
              href={`tel:${SITE_PHONE_HREF}`}
              aria-label={`Позвонить по номеру ${SITE_PHONE}`}
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M7.2 3.5 10 7.1 8.5 9.4c1.4 2.7 3.4 4.7 6.1 6.1l2.3-1.5 3.6 2.8-.8 2.7c-.2.7-.9 1.1-1.6 1-7.7-1-13.6-6.9-14.6-14.6-.1-.7.3-1.4 1-1.6l2.7-.8Z" />
              </svg>
              <span>Позвонить</span>
            </a>
          </div>

          <button
            className="sdBurger"
            type="button"
            aria-label={isOpen ? "Закрыть меню" : "Открыть меню"}
            aria-expanded={isOpen}
            onClick={toggleMobileMenu}
          >
            <span className={isOpen ? "active" : ""} />
            <span className={isOpen ? "active" : ""} />
            <span className={isOpen ? "active" : ""} />
          </button>
        </div>
      </div>

      <div className="sdHeaderNavBar">
        <div className="container sdHeaderNavInner">
          <nav className="sdDesktopNav" aria-label="Основное меню">
            <div
              className={`sdNavDropdown ${
                openDropdown === "catalog" ? "isOpen" : ""
              }`}
              onMouseEnter={() => setOpenDropdown("catalog")}
              onMouseLeave={() => setOpenDropdown(null)}
            >
              <button
                aria-expanded={openDropdown === "catalog"}
                className="sdNavDropdownTrigger"
                onClick={() =>
                  setOpenDropdown((current) =>
                    current === "catalog" ? null : "catalog"
                  )
                }
                type="button"
              >
                Каталог
                <SiteIcon className="sdNavChevron" name="chevron" />
              </button>

              {openDropdown === "catalog" && (
                <div className="sdNavDropdownMenu sdNavDropdownMenuText">
                  {CATALOG_LINKS.map((item) => (
                    <Link href={item.href} key={item.href} onClick={closeMenu}>
                      <strong>{item.title}</strong>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <Link href="/calculator" onClick={closeMenu}>
              Калькулятор
            </Link>
            <Link href="/portfolio" onClick={closeMenu}>
              Портфолио
            </Link>

            <div
              className={`sdNavDropdown ${
                openDropdown === "company" ? "isOpen" : ""
              }`}
              onMouseEnter={() => setOpenDropdown("company")}
              onMouseLeave={() => setOpenDropdown(null)}
            >
              <button
                aria-expanded={openDropdown === "company"}
                className="sdNavDropdownTrigger"
                onClick={() =>
                  setOpenDropdown((current) =>
                    current === "company" ? null : "company"
                  )
                }
                type="button"
              >
                О компании
                <SiteIcon className="sdNavChevron" name="chevron" />
              </button>

              {openDropdown === "company" && (
                <div className="sdNavDropdownMenu sdNavDropdownMenuText">
                  {companyLinks.map((item) => (
                    <Link href={item.href} key={item.href} onClick={closeMenu}>
                      <strong>{item.title}</strong>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <Link href="/kontakty" onClick={closeMenu}>
              Контакты
            </Link>

            <div
              className={`sdNavDropdown ${
                openDropdown === "guide" ? "isOpen" : ""
              }`}
              onMouseEnter={() => setOpenDropdown("guide")}
              onMouseLeave={() => setOpenDropdown(null)}
            >
              <button
                aria-expanded={openDropdown === "guide"}
                className="sdNavDropdownTrigger"
                onClick={() =>
                  setOpenDropdown((current) =>
                    current === "guide" ? null : "guide"
                  )
                }
                type="button"
              >
                Справочник
                <SiteIcon className="sdNavChevron" name="chevron" />
              </button>

              {openDropdown === "guide" && (
                <div className="sdNavDropdownMenu sdNavDropdownMenuText sdGuideDropdownMenu">
                  {guideLinks.map((item) => (
                    <Link href={item.href} key={item.href} onClick={closeMenu}>
                      <strong>{item.title}</strong>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <Link href="/faq" onClick={closeMenu}>
              FAQ
            </Link>
            <Link href="/otzyvy" onClick={closeMenu}>
              Отзывы
            </Link>
          </nav>

          <Link className="sdHeaderCalc" href="/calculator">
            Рассчитать стоимость
          </Link>
        </div>
      </div>

      {isOpen && (
        <nav className="sdMobileMenu" aria-label="Мобильное меню">
          <div className="container sdMobileMenuInner">
            <div className="sdMobileMenuIntro">
              <span>Меню</span>
              <small>Проекты, услуги и полезная информация</small>
            </div>

            <div className="sdMobileNavPanel">
              <div className="sdMobileMenuSection">
                <button
                  aria-expanded={openDropdown === "catalog"}
                  className="sdMobileCatalogToggle"
                  onClick={() =>
                    setOpenDropdown((current) =>
                      current === "catalog" ? null : "catalog"
                    )
                  }
                  type="button"
                >
                  <span className="sdMobileNavLabel">
                    <span className="sdMobileNavIcon">
                      <SiteIcon name="house" />
                    </span>
                    <span>
                      <strong>Каталог проектов</strong>
                      <small>Дома и бани из бруса</small>
                    </span>
                  </span>
                  <SiteIcon className="sdNavChevron" name="chevron" />
                </button>

                {openDropdown === "catalog" && (
                  <div className="sdMobileSubmenuLinks sdMobileCatalogSubmenu">
                    {CATALOG_LINKS.map((item) => (
                      <Link href={item.href} key={item.href} onClick={closeMenu}>
                        <span className="sdMobileSubmenuIcon">
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

              <Link
                className="sdMobileDirectLink"
                href="/calculator"
                onClick={closeMenu}
              >
                <span className="sdMobileNavIcon">
                  <SiteIcon name="price" />
                </span>
                <span>
                  <strong>Калькулятор</strong>
                  <small>Предварительный расчёт</small>
                </span>
                <span className="sdMobileLinkArrow" aria-hidden="true">
                  →
                </span>
              </Link>

              <Link
                className="sdMobileDirectLink"
                href="/portfolio"
                onClick={closeMenu}
              >
                <span className="sdMobileNavIcon">
                  <SiteIcon name="blueprint" />
                </span>
                <span>
                  <strong>Портфолио</strong>
                  <small>Построенные объекты</small>
                </span>
                <span className="sdMobileLinkArrow" aria-hidden="true">
                  →
                </span>
              </Link>

              <div className="sdMobileMenuSection">
                <button
                  aria-expanded={openDropdown === "company"}
                  className="sdMobileCatalogToggle"
                  onClick={() =>
                    setOpenDropdown((current) =>
                      current === "company" ? null : "company"
                    )
                  }
                  type="button"
                >
                  <span className="sdMobileNavLabel">
                    <span className="sdMobileNavIcon">
                      <SiteIcon name="factory" />
                    </span>
                    <span>
                      <strong>О компании</strong>
                      <small>Производство и условия</small>
                    </span>
                  </span>
                  <SiteIcon className="sdNavChevron" name="chevron" />
                </button>

                {openDropdown === "company" && (
                  <div className="sdMobileSubmenuLinks">
                    {companyLinks.map((item) => (
                      <Link href={item.href} key={item.href} onClick={closeMenu}>
                        <strong>{item.title}</strong>
                        <span aria-hidden="true">→</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              <Link
                className="sdMobileDirectLink"
                href="/kontakty"
                onClick={closeMenu}
              >
                <span className="sdMobileNavIcon">
                  <SiteIcon name="contract" />
                </span>
                <span>
                  <strong>Контакты</strong>
                  <small>Телефон, адрес и реквизиты</small>
                </span>
                <span className="sdMobileLinkArrow" aria-hidden="true">
                  →
                </span>
              </Link>

              <div className="sdMobileMenuSection">
                <button
                  aria-expanded={openDropdown === "guide"}
                  className="sdMobileCatalogToggle"
                  onClick={() =>
                    setOpenDropdown((current) =>
                      current === "guide" ? null : "guide"
                    )
                  }
                  type="button"
                >
                  <span className="sdMobileNavLabel">
                    <span className="sdMobileNavIcon">
                      <SiteIcon name="blueprint" />
                    </span>
                    <span>
                      <strong>Справочник</strong>
                      <small>Статьи о строительстве</small>
                    </span>
                  </span>
                  <SiteIcon className="sdNavChevron" name="chevron" />
                </button>

                {openDropdown === "guide" && (
                  <div className="sdMobileSubmenuLinks">
                    {guideLinks.map((item) => (
                      <Link href={item.href} key={item.href} onClick={closeMenu}>
                        <strong>{item.title}</strong>
                        <span aria-hidden="true">→</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              <Link
                className="sdMobileDirectLink"
                href="/faq"
                onClick={closeMenu}
              >
                <span className="sdMobileNavIcon">
                  <SiteIcon name="shield" />
                </span>
                <span>
                  <strong>Частые вопросы</strong>
                  <small>Коротко о важном</small>
                </span>
                <span className="sdMobileLinkArrow" aria-hidden="true">
                  →
                </span>
              </Link>

              <Link
                className="sdMobileDirectLink"
                href="/otzyvy"
                onClick={closeMenu}
              >
                <span className="sdMobileNavIcon">
                  <SiteIcon name="gift" />
                </span>
                <span>
                  <strong>Отзывы</strong>
                  <small>Опыт наших заказчиков</small>
                </span>
                <span className="sdMobileLinkArrow" aria-hidden="true">
                  →
                </span>
              </Link>
            </div>

            <div className="sdMobileContactCard">
              <div className="sdMobileContactRow">
                <div>
                  <small>Звоните — поможем с выбором</small>
                  <a href={`tel:${SITE_PHONE_HREF}`} onClick={closeMenu}>
                    {SITE_PHONE}
                  </a>
                  <span>Ежедневно с 9:00 до 20:00</span>
                </div>
                <SocialLinks />
              </div>
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
