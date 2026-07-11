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
      <div className="container footerTop">
        <div className="footerBrand">
          <Link className="sdLogo footerLogo" href="/">
            <span className="sdLogoMark">⌂</span>
            <span className="sdLogoText">
              <strong>Домодел44</strong>
              <small>строительство из дерева</small>
            </span>
          </Link>

          <p>
            Проектируем и строим дома, бани и гаражи из бруса. Подбираем
            комплектацию, считаем доставку и фиксируем смету до начала работ.
          </p>

          <Link className="buttonPrimary footerButton" href="/#lead-form">
            Рассчитать стоимость
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
            {landingPages.slice(0, 7).map((page) => (
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
              <a href="mailto:info@stroidacha.local">info@stroidacha.local</a>
            </li>
            <li>
              <span>Время работы</span>
              <strong>Ежедневно, 9:00–20:00</strong>
            </li>
          </ul>
        </div>
      </div>

      <div className="container footerBottom">
        <span>© {new Date().getFullYear()} Домодел44</span>
        <span>Информация на сайте не является публичной офертой.</span>
      </div>
    </footer>
  );
}
