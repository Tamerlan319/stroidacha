"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

import { CATALOG_LINKS, SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";
import BrandMark from "./BrandMark";
import SiteIcon from "./SiteIcon";

const menuItems = [
  { title: "Портфолио", href: "/portfolio" },
  { title: "Калькулятор", href: "/calculator" },
  { title: "Производство", href: "/proizvodstvo" },
  { title: "Контакты", href: "/kontakty" },
];

const socialLinks = [
  {
    title: "WhatsApp",
    href: "https://api.whatsapp.com/send?phone=79676801812",
    icon: "whatsapp",
  },
  {
    title: "Viber",
    href: "viber://chat?number=79676801812",
    icon: "viber",
  },
] as const;

function SocialIcon({ name }: { name: "whatsapp" | "viber" }) {
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
          target={item.icon === "whatsapp" ? "_blank" : undefined}
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
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [phone, setPhone] = useState("");
  const [formStatus, setFormStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const catalogRef = useRef<HTMLDivElement>(null);
  const mobileMenuRef = useRef<HTMLElement>(null);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node;
      const isInsideDesktopCatalog = catalogRef.current?.contains(target);
      const isInsideMobileMenu = mobileMenuRef.current?.contains(target);

      if (!isInsideDesktopCatalog && !isInsideMobileMenu) {
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

  function toggleMobileMenu() {
    setIsOpen((current) => {
      if (current) setIsCatalogOpen(false);
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
    <header className="sdHeader">
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
                Каталог проектов
                <SiteIcon className="sdNavChevron" name="chevron" />
              </button>

              {isCatalogOpen && (
                <div className="sdNavDropdownMenu">
                  {CATALOG_LINKS.map((item) => (
                    <Link href={item.href} key={item.href} onClick={closeMenu}>
                      <span className="sdNavDropdownIcon"><SiteIcon name={item.icon} /></span>
                      <span><strong>{item.title}</strong><small>{item.description}</small></span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {menuItems.map((item) => (
              <Link href={item.href} key={item.href} onClick={closeMenu}>{item.title}</Link>
            ))}
          </nav>

          <Link className="sdHeaderCalc" href="/calculator">Рассчитать стоимость</Link>
        </div>
      </div>

      {isOpen && (
        <nav className="sdMobileMenu" aria-label="Мобильное меню" ref={mobileMenuRef}>
          <div className="container sdMobileMenuInner">
            <button
              aria-expanded={isCatalogOpen}
              className="sdMobileCatalogToggle"
              onClick={() => setIsCatalogOpen((current) => !current)}
              type="button"
            >
              Каталог проектов
              <SiteIcon className="sdNavChevron" name="chevron" />
            </button>

            {isCatalogOpen && (
              <div className="sdMobileCatalogLinks">
                {CATALOG_LINKS.map((item) => (
                  <Link href={item.href} key={item.href} onClick={closeMenu}>
                    <SiteIcon name={item.icon} />
                    <span><strong>{item.title}</strong><small>{item.description}</small></span>
                  </Link>
                ))}
              </div>
            )}

            <div className="sdMobilePrimaryLinks">
              {menuItems.map((item) => (
                <Link href={item.href} key={item.href} onClick={closeMenu}>{item.title}</Link>
              ))}
            </div>

            <div className="sdMobileContactRow">
              <div>
                <a href={`tel:${SITE_PHONE_HREF}`} onClick={closeMenu}>{SITE_PHONE}</a>
                <small>Ежедневно с 9:00 до 20:00</small>
              </div>
              <SocialLinks />
            </div>

            {renderQuickForm("sdMobileQuickForm")}
          </div>
        </nav>
      )}
    </header>
  );
}
