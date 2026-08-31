import Link from "next/link";

export type BreadcrumbItem = {
  name: string;
  // Без href — текущая страница, рендерится как обычный текст, не ссылка.
  href?: string;
};

type BreadcrumbsProps = {
  items: BreadcrumbItem[];
};

// Один источник данных для видимой навигации и BreadcrumbList в JSON-LD —
// строит их вызывающая страница (buildBreadcrumbItems в конкретном
// page.tsx) и передаёт один и тот же массив сюда и в JsonLd, чтобы
// видимые крошки никогда не разошлись со структурированными данными.
export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  if (items.length < 2) {
    return null;
  }

  return (
    <nav aria-label="Хлебные крошки" className="container breadcrumbs">
      <ol>
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={`${item.name}-${index}`}>
              {item.href && !isLast ? (
                <Link href={item.href}>{item.name}</Link>
              ) : (
                <span aria-current={isLast ? "page" : undefined}>
                  {item.name}
                </span>
              )}
              {!isLast && (
                <span aria-hidden="true" className="breadcrumbsDivider">
                  /
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
