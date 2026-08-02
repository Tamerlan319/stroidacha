type SiteIconProps = {
  name?: string | null;
  className?: string;
};

type IconName =
  | "blueprint"
  | "chevron"
  | "factory"
  | "foundation"
  | "gift"
  | "house"
  | "contract"
  | "price"
  | "shield"
  | "truck";

const aliases: Record<string, IconName> = {
  "⌂": "house",
  "▣": "blueprint",
  "↗": "truck",
  "♨": "factory",
  blueprint: "blueprint",
  cost: "price",
  delivery: "truck",
  factory: "factory",
  foundation: "foundation",
  gift: "gift",
  contract: "contract",
  home: "house",
  house: "house",
  money: "price",
  plan: "blueprint",
  price: "price",
  production: "factory",
  project: "blueprint",
  projects: "blueprint",
  quality: "shield",
  shield: "shield",
  truck: "truck",
  доставка: "truck",
  дом: "house",
  завод: "factory",
  проект: "blueprint",
  производство: "factory",
  цена: "price",
};

function resolveIconName(name?: string | null): IconName {
  if (!name) {
    return "house";
  }

  return aliases[name.trim().toLowerCase()] || "house";
}

export default function SiteIcon({ name, className }: SiteIconProps) {
  const iconName = name === "chevron" ? "chevron" : resolveIconName(name);

  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      focusable="false"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      viewBox="0 0 24 24"
    >
      {iconName === "house" && (
        <>
          <path d="M3.5 11.2 12 4l8.5 7.2" />
          <path d="M5.5 10.4V20h13v-9.6M9.5 20v-6h5v6" />
        </>
      )}

      {iconName === "blueprint" && (
        <>
          <path d="M4 5.5h16v13H4z" />
          <path d="M8 5.5v13M8 10h7M15 10v8.5M8 14h4" />
        </>
      )}

      {iconName === "truck" && (
        <>
          <path d="M3 6h11v10H3zM14 9h3.5l3.5 3.5V16h-7z" />
          <path d="M7 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM18 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
        </>
      )}

      {iconName === "factory" && (
        <>
          <path d="M3 20V10l6 3V9l6 3V4h4l2 16z" />
          <path d="M7 16h2M12 16h2M17 16h2" />
        </>
      )}

      {iconName === "foundation" && (
        <>
          <path d="M4 5h16v4H4zM6 9v10M18 9v10M3 19h18" />
          <path d="M9 9v5M15 9v5M4 14h16" />
        </>
      )}

      {iconName === "gift" && (
        <>
          <path d="M4 10h16v10H4zM3 7h18v3H3zM12 7v13" />
          <path d="M12 7H8.5a2.5 2.5 0 1 1 2.2-3.7L12 7Zm0 0h3.5a2.5 2.5 0 1 0-2.2-3.7L12 7Z" />
        </>
      )}

      {iconName === "contract" && (
        <>
          <path d="M6 3.5h9l3 3V20H6zM15 3.5V7h3" />
          <path d="M9 11h6M9 14h6M9 17h4" />
        </>
      )}

      {iconName === "price" && (
        <>
          <path d="M4 6.5h16v11H4z" />
          <path d="M7 10h4.3a2 2 0 1 1 0 4H8.5V9M8.5 15.5v-8M7 14h5.5" />
          <path d="M16.5 12h.01" />
        </>
      )}

      {iconName === "shield" && (
        <>
          <path d="M12 3.5 19 6v5c0 4.4-2.8 7.5-7 9.5C7.8 18.5 5 15.4 5 11V6z" />
          <path d="m8.5 12 2.2 2.2 4.8-5" />
        </>
      )}

      {iconName === "chevron" && <path d="m7 9.5 5 5 5-5" />}
    </svg>
  );
}
