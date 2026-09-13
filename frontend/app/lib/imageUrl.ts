import type { CSSProperties } from "react";

// Адрес картинки через оптимизатор next/image (/_next/image) — для фонов в
// CSS, где компонент Image не подходит: браузер получает WebP нужной ширины
// вместо исходного файла. width — из стандартных deviceSizes Next (640, 750,
// 828, 1080, 1200, 1920, …), q=75 — единственное разрешённое по умолчанию
// качество в Next 16. Хост внешней картинки должен быть в images.remotePatterns.
export function optimizedImageUrl(src: string, width: number) {
  // Относительный адрес (например, /media/… без домена) оптимизатор Next
  // искал бы у себя и не нашёл — такой отдаём как есть.
  if (!/^https?:\/\//.test(src)) return src;
  return `/_next/image?url=${encodeURIComponent(src)}&w=${width}&q=75`;
}

// Фон первого экрана из фото (страница проекта): CSS берёт --hero-image, на
// телефоне — --hero-image-mobile (см. .projectHeroCover в globals.css).
// Раньше в фон шёл исходный файл из /media — 300–900 КБ на любом экране.
export function heroBackgroundStyle(
  src: string | null | undefined,
): CSSProperties | undefined {
  if (!src) return undefined;

  return {
    "--hero-image": `url("${optimizedImageUrl(src, 1920)}")`,
    "--hero-image-mobile": `url("${optimizedImageUrl(src, 1080)}")`,
  } as CSSProperties;
}
