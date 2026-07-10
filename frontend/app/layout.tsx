import type { Metadata } from "next";
import "./globals.css";

import SiteFooter from "./components/SiteFooter";
import SiteHeader from "./components/SiteHeader";

import MobileHorizontalLock from "./components/MobileScrollFix";

export const metadata: Metadata = {
  title: "СтройДача — дома, бани и гаражи из бруса",
  description:
    "Строительство домов, бань и гаражей из бруса. Готовые проекты, комплектации, расчёт стоимости и доставка по России.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>
        <MobileHorizontalLock />
        <SiteHeader />

        {children}

        <SiteFooter />
      </body>
    </html>
  );
}