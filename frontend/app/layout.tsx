import type { Metadata } from "next";
import "./globals.css";

import SiteFooter from "./components/SiteFooter";
import SiteHeader from "./components/SiteHeader";

import MobileHorizontalLock from "./components/MobileScrollFix";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://brusoteka.ru",
  ),
  title: "Брусотека — строительство домов из бруса под ключ",
  description:
    "Строительство домов, бань и гаражей из бруса под ключ в России. Готовые проекты, комплектации и расчёт стоимости.",
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
