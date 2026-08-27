"use client";

import { createContext, useContext } from "react";

export type SocialLinkData = {
  platform: string;
  url: string;
};

const SocialLinksContext = createContext<SocialLinkData[]>([]);

type SocialLinksProviderProps = {
  links: SocialLinkData[];
  children: React.ReactNode;
};

// Ссылки на соцсети загружаются один раз в layout.tsx (Django Admin →
// SocialLink) и раздаются через контекст всем местам, где нужен
// SocialLinks (шапка, форма заявки, попап в баннере) — без повторного
// запроса на каждый компонент.
export function SocialLinksProvider({ links, children }: SocialLinksProviderProps) {
  return (
    <SocialLinksContext.Provider value={links}>
      {children}
    </SocialLinksContext.Provider>
  );
}

export function useSocialLinks() {
  return useContext(SocialLinksContext);
}
