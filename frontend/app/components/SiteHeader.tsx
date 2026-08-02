"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

import { CATALOG_LINKS, SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";
import BrandMark from "./BrandMark";
import SiteIcon from "./SiteIcon";

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

const socialLinks = [
  {
    title: "ВКонтакте",
    href: process.env.NEXT_PUBLIC_VK_URL || "https://vk.com/",
    icon: "vk",
  },
  {
    title: "WhatsApp",
    href: "https://api.whatsapp.com/send?phone=79676801812",
    icon: "whatsapp",
  },
  {
    title: "Telegram",
    href: process.env.NEXT_PUBLIC_TELEGRAM_URL || "https://t.me/+79676801812",
    icon: "telegram",
  },
  {
    title: "Viber",
    href: "viber://chat?number=79676801812",
    icon: "viber",
  },
  {
    title: "Одноклассники",
    href: process.env.NEXT_PUBLIC_OK_URL || "https://ok.ru/",
    icon: "ok",
  },
] as const;

type SocialName = (typeof socialLinks)[number]["icon"];

function SocialIcon({ name }: { name: SocialName }) {
  if (name === "vk" || name === "ok") {
    return (
      <span className="sdSocialMonogram" aria-hidden="true">
        {name === "vk" ? "VK" : "OK"}
      </span>
    );
  }

  if (name === "telegram") {
    return (
      <svg aria-hidden="true" viewBox="0 0 24 24">
        <path d="m3.2 11.2 16.1-6.3c.8-.3 1.5.2 1.2 1.5l-2.7 12.7c-.2.9-.8 1.1-1.6.7l-4.1-3-2 1.9c-.2.2-.4.4-.8.4l.3-4.2 7.7-7c.3-.3-.1-.5-.5-.2L7.3 13.7l-4.1-1.3c-.9-.3-.9-.9 0-1.2Z" />
      </svg>
    );
  }

  if (name === "whatsapp") {
    return (
      <svg aria-hidden="true" viewBox="0 0 24 24">
        <path d="M12 3a8.2 8.2 0 0 0-7 12.4L4 20l4.7-1.2A8.2 8.2 0 1 0 12 3Z" />
        <path d="M8.7 8.1c.2-.5.4-.5.7-.5h.5c.2 0 .3.1.4.4l.7 1.7c.1.3 0 .4-.1.6l-.5.7c-.2.2-.1.4 0 .6.6 1 1.5 1.8 2.5 2.3.2.1.4.1.6-.1l.8-1c.2-.2.4-.2.6-.1l1.7.8c.3.1.4.3.4.5 0 .2-.1 1.2-.7 1.7-.5.5-1.2.8-2 .8-1 0-2.5-.5-4.1-1.8-2-1.6-3.2-3.9-3.3-5.3 0-.7.2-1.1.5-1.5.3-.3.6-.5.8-.5Z" />
      </svg>
    );
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M6.1 4.7c3.8-2 9.9-1.2 11.7.8 1.8 2.1 2 7 .6 9.4-.8 1.4-2.3 2.1-4 2.5l-2.4 2v-1.7c-2.6.1-5.1-.3-6.3-1.6-2.2-2.3-2.4-9.3.4-11.4Z" />
      <path d="M8.3 7.5c.3-.3.7-.4 1-.1l1 1.4c.2.3.2.6 0 .8l-.5.6c.5 1 1.4 1.9 2.4 2.4l.7-.6c.2-.2.5-.2.8 0l1.3 1c.3.2.3.6.1.9-.5.8-1.2 1.2-2 1-2.7-.5-6-3.8-6.4-6.4-.1-.4.7-1 .6-1Z" />
      <path d="M12.2 6.6c2.1.2 3.4 1.5 3.6 3.6M12.1 8.2c1.1.1 1.9.8 2 2" />
    </svg>
  );
}

function SocialLinks({ className = "" }: { className?: string }) {
  return (
    <div className={`sdSocialLinks ${className}`} aria-label="Связаться в мессенджерах">
      {socialLinks.map((item) => (
        <a
          aria-label={item.title}
          href={item.href}
          key={item.title}
          rel="noopener noreferrer"
          target={item.href.startsWith("http") ? "_blank" : undefined}
          title={item.title}
        >
          <SocialIcon name={item.icon} />
        </a>
      ))}
    </div>
  );
}

export default function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<
    "catalog" | "company" | "guide" | null
  >(null);
  const [guideLinks, setGuideLinks] = useState<HeaderLink[]>([
    { title: "Все статьи", href: "/spravochnik" },
  ]);
  const [phone, setPhone] = useState("");
  const [formStatus, setFormStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
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
        if (!response.ok) return;
        const pages = (await response.json()) as LandingPageListItem[];
        const articles = pages
          .filter((page) => page.page_type === "guide")
          .sort((a, b) => a.sort_order - b.sort_order)
          .map((page) => ({ title: page.title, href: `/${page.slug}` }));

        if (!isCancelled) {
          setGuideLinks([
            { title: "Все статьи", href: "/spravochnik" },
            ...articles,
          ]);
        }
      } catch {
        // Справочник остаётся доступен даже при временной недоступности API.
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
      if (current) setOpenDropdown(null);
      return !current;
    });
  }

  async function handleQuickCallback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!phone.trim() || formStatus === "submitting") return;

    setFormStatus("submitting");

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/leads/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "Заявка из шапки",
          phone,
          email: "",
          message: "Телефонная консультация и предварительный расчёт",
          source: "callback",
          project_slug: "",
          page_url: window.location.href,
        }),
      });

      if (!response.ok) throw new Error("Не удалось отправить заявку");
      setPhone("");
      setFormStatus("success");
    } catch {
      setFormStatus("error");
    }
  }

  function renderQuickForm(className = "") {
    return (
      <form className={`sdHeaderQuickForm ${className}`} onSubmit={handleQuickCallback}>
        <label>
          <span>Консультация и расчёт</span>
          <input
            aria-label="Номер телефона"
            inputMode="tel"
            onChange={(event) => {
              setPhone(event.target.value);
              if (formStatus !== "idle") setFormStatus("idle");
            }}
            placeholder="+7 (___) ___-__-__"
            required
            type="tel"
            value={phone}
          />
        </label>
        <button disabled={formStatus === "submitting"} type="submit">
          {formStatus === "submitting" ? "Отправляем…" : "Перезвоните мне"}
        </button>
        {formStatus === "success" && <small className="isSuccess">Заявка отправлена</small>}
        {formStatus === "error" && <small className="isError">Не удалось отправить</small>}
      </form>
    );
  }

  return (
    <header className="sdHeader" ref={headerRef}>
      <div className="sdHeaderMain">
        <div className="container sdHeaderInner">
          <Link className="sdLogo" href="/" onClick={closeMenu}>
            <span className="sdLogoMark"><BrandMark /></span>
            <span className="sdLogoText">
              <strong>Брусотека</strong>
              <small>строим дома из бруса</small>
            </span>
          </Link>

          <p className="sdHeaderPromise">Дома и бани из бруса<br />от производителя</p>
          <SocialLinks className="sdHeaderSocials" />

          <div className="sdHeaderContacts">
            <a className="sdPhone" href={`tel:${SITE_PHONE_HREF}`}>{SITE_PHONE}</a>
            <small>Ежедневно с 9:00 до 20:00</small>
          </div>

          {renderQuickForm()}

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
              className={`sdNavDropdown ${openDropdown === "catalog" ? "isOpen" : ""}`}
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

            <Link href="/calculator" onClick={closeMenu}>Калькулятор</Link>
            <Link href="/portfolio" onClick={closeMenu}>Портфолио</Link>

            <div
              className={`sdNavDropdown ${openDropdown === "company" ? "isOpen" : ""}`}
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

            <Link href="/kontakty" onClick={closeMenu}>Контакты</Link>

            <div
              className={`sdNavDropdown ${openDropdown === "guide" ? "isOpen" : ""}`}
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

            <Link href="/faq" onClick={closeMenu}>FAQ</Link>
            <Link href="/otzyvy" onClick={closeMenu}>Отзывы</Link>
          </nav>

          <Link className="sdHeaderCalc" href="/calculator">Рассчитать стоимость</Link>
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
                    <span className="sdMobileNavIcon"><SiteIcon name="house" /></span>
                    <span><strong>Каталог проектов</strong><small>Дома и бани из бруса</small></span>
                  </span>
                  <SiteIcon className="sdNavChevron" name="chevron" />
                </button>

                {openDropdown === "catalog" && (
                  <div className="sdMobileSubmenuLinks sdMobileCatalogSubmenu">
                    {CATALOG_LINKS.map((item) => (
                      <Link href={item.href} key={item.href} onClick={closeMenu}>
                        <span className="sdMobileSubmenuIcon"><SiteIcon name={item.icon} /></span>
                        <span><strong>{item.title}</strong><small>{item.description}</small></span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              <Link className="sdMobileDirectLink" href="/calculator" onClick={closeMenu}>
                <span className="sdMobileNavIcon"><SiteIcon name="price" /></span>
                <span><strong>Калькулятор</strong><small>Предварительный расчёт</small></span>
                <span className="sdMobileLinkArrow" aria-hidden="true">→</span>
              </Link>

              <Link className="sdMobileDirectLink" href="/portfolio" onClick={closeMenu}>
                <span className="sdMobileNavIcon"><SiteIcon name="blueprint" /></span>
                <span><strong>Портфолио</strong><small>Построенные объекты</small></span>
                <span className="sdMobileLinkArrow" aria-hidden="true">→</span>
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
                    <span className="sdMobileNavIcon"><SiteIcon name="factory" /></span>
                    <span><strong>О компании</strong><small>Производство и условия</small></span>
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

              <Link className="sdMobileDirectLink" href="/kontakty" onClick={closeMenu}>
                <span className="sdMobileNavIcon"><SiteIcon name="contract" /></span>
                <span><strong>Контакты</strong><small>Телефон, адрес и реквизиты</small></span>
                <span className="sdMobileLinkArrow" aria-hidden="true">→</span>
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
                    <span className="sdMobileNavIcon"><SiteIcon name="blueprint" /></span>
                    <span><strong>Справочник</strong><small>Статьи о строительстве</small></span>
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

              <Link className="sdMobileDirectLink" href="/faq" onClick={closeMenu}>
                <span className="sdMobileNavIcon"><SiteIcon name="shield" /></span>
                <span><strong>Частые вопросы</strong><small>Коротко о важном</small></span>
                <span className="sdMobileLinkArrow" aria-hidden="true">→</span>
              </Link>

              <Link className="sdMobileDirectLink" href="/otzyvy" onClick={closeMenu}>
                <span className="sdMobileNavIcon"><SiteIcon name="gift" /></span>
                <span><strong>Отзывы</strong><small>Опыт наших заказчиков</small></span>
                <span className="sdMobileLinkArrow" aria-hidden="true">→</span>
              </Link>
            </div>

            <div className="sdMobileContactCard">
              <div className="sdMobileContactRow">
                <div>
                  <small>Звоните — поможем с выбором</small>
                  <a href={`tel:${SITE_PHONE_HREF}`} onClick={closeMenu}>{SITE_PHONE}</a>
                  <span>Ежедневно с 9:00 до 20:00</span>
                </div>
                <SocialLinks />
              </div>

              {renderQuickForm("sdMobileQuickForm")}
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
