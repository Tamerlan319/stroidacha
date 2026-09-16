import Link from "next/link";

import { CATALOG_LINKS, COMPANY_LINKS, SITE_EMAIL } from "../lib/site";
import BrandMark from "./BrandMark";
import FooterLegalBlock from "./FooterLegalBlock";
import FooterPhoneLink from "./FooterPhoneLink";

// Раньше «Направления» брали первые семь SEO-страниц из API — туда попадали
// дубли каталога и «Доставка по России» вместо страницы «Доставка». Теперь
// в подвале те же страницы о компании, что в меню шапки (COMPANY_LINKS).
export default function SiteFooter() {
  return (
    <footer className="siteFooter">
      <div className="container footerTop">
        <div className="footerBrand">
          <Link className="sdLogo footerLogo" href="/">
            <span className="sdLogoMark">
              <BrandMark />
            </span>
            <span className="sdLogoText">
              <strong>Брусодел</strong>
              <small>строительство из дерева</small>
            </span>
          </Link>

          <p>
            Проектируем и строим дома и бани из бруса. Подбираем
            комплектацию, считаем доставку и фиксируем смету до начала работ.
          </p>

          <Link className="buttonPrimary footerButton" href="/calculator">
            Рассчитать стоимость
          </Link>
        </div>

        <div>
          <h3>Каталог</h3>
          <ul className="footerLinks">
            {CATALOG_LINKS.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.title}</Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3>Направления</h3>
          <ul className="footerLinks">
            <li><Link href="/portfolio">Портфолио</Link></li>
            <li><Link href="/otzyvy">Отзывы</Link></li>
            <li><Link href="/faq">FAQ</Link></li>
            <li><Link href="/spravochnik">Справочник</Link></li>
            {COMPANY_LINKS.map((item) => (
              <li key={item.href}>
                <Link href={item.href}>{item.title}</Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3>Контакты</h3>
          <ul className="footerContacts">
            <li>
              <span>Телефон</span>
              <FooterPhoneLink />
            </li>
            <li>
              <span>Email</span>
              <a href={`mailto:${SITE_EMAIL}`}>{SITE_EMAIL}</a>
            </li>
            <li>
              <span>Время работы</span>
              <strong>Ежедневно, 9:00–20:00</strong>
            </li>
          </ul>
        </div>
      </div>

      <div className="container">
        <FooterLegalBlock />
      </div>

      <div className="container footerBottom">
        <span>© {new Date().getFullYear()} ООО «СтройДача»</span>
        <span>«Брусодел» — бренд ООО «СтройДача».</span>
        <span>Информация на сайте не является публичной офертой.</span>
      </div>
    </footer>
  );
}
