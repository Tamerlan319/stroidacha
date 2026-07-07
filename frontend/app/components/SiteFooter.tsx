import Link from "next/link";

type LandingPage = {
  id: number;
  title: string;
  slug: string;
  h1: string;
  page_type: string;
};

async function getLandingPages(): Promise<LandingPage[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  try {
    const response = await fetch(`${apiUrl}/landing-pages/`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return [];
    }

    return response.json();
  } catch {
    return [];
  }
}

export default async function SiteFooter() {
  const landingPages = await getLandingPages();

  return (
    <footer className="siteFooter">
      <div className="container footerGrid">
        <div className="footerBrand">
          <Link className="logo footerLogo" href="/">
            <span className="logoMark">СД</span>
            <span>
              <strong>СтройДача</strong>
              <small>строительство из дерева</small>
            </span>
          </Link>

          <p>
            Дома, бани и гаражи из бруса с понятными комплектациями,
            расчётом стоимости и доставкой по России.
          </p>

          <Link className="buttonPrimary footerButton" href="/#lead-form">
            Оставить заявку
          </Link>
        </div>

        <div>
          <h3>Каталог</h3>
          <ul className="footerLinks">
            <li>
              <Link href="/doma-iz-brusa">Дома из бруса</Link>
            </li>
            <li>
              <Link href="/bani-iz-brusa">Бани из бруса</Link>
            </li>
            <li>
              <Link href="/garazhi-pod-klyuch">Гаражи</Link>
            </li>
            <li>
              <Link href="/doma-iz-brusa-pod-usadku">Дома под усадку</Link>
            </li>
          </ul>
        </div>

        <div>
          <h3>Направления</h3>
          <ul className="footerLinks">
            {landingPages.slice(0, 8).map((page) => (
              <li key={page.id}>
                <Link href={`/${page.slug}`}>{page.h1 || page.title}</Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3>Контакты</h3>
          <ul className="footerContacts">
            <li>
              <span>Телефон</span>
              <a href="tel:+79999999999">+7 999 999-99-99</a>
            </li>
            <li>
              <span>Email</span>
              <a href="mailto:info@stroidacha.local">
                info@stroidacha.local
              </a>
            </li>
            <li>
              <span>Режим работы</span>
              <strong>Пн–Сб, 9:00–19:00</strong>
            </li>
          </ul>
        </div>
      </div>

      <div className="container footerBottom">
        <span>© {new Date().getFullYear()} СтройДача</span>
        <span>Информация на сайте не является публичной офертой.</span>
      </div>
    </footer>
  );
}