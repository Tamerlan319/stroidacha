// Метки рекламной кампании для заявки.
//
// Раньше LeadForm читал utm_* прямо из адресной строки в момент отправки —
// метки терялись при любом переходе по сайту и когда каталог переписывал
// адрес под фильтры. Теперь они запоминаются при входе на сайт (UtmCapture в
// layout.tsx) и живут до закрытия вкладки.
//
// sessionStorage, а не cookie: сам по себе ничего на сервер не уходит и за
// пределы сессии не живёт — метки отправляются только вместе с заявкой,
// которую человек оставляет сам. UTM-метки прямо перечислены в политике
// обработки ПДн (раздел 2), так что это в рамках уже заявленного.

export const UTM_KEYS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
] as const;

export type UtmKey = (typeof UTM_KEYS)[number];

type UtmSet = Partial<Record<UtmKey, string>>;

const STORAGE_KEY = "brusodel-utm";

function readUtmFromUrl(): UtmSet {
  const params = new URLSearchParams(window.location.search);
  const found: UtmSet = {};

  for (const key of UTM_KEYS) {
    const value = params.get(key);
    if (value) {
      found[key] = value;
    }
  }

  return found;
}

function readStoredUtm(): UtmSet {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : null;
    if (!parsed || typeof parsed !== "object") {
      return {};
    }

    const found: UtmSet = {};
    for (const key of UTM_KEYS) {
      const value = (parsed as Record<string, unknown>)[key];
      if (typeof value === "string" && value) {
        found[key] = value;
      }
    }
    return found;
  } catch {
    // Приватный режим, запрет хранилища или испорченное значение.
    return {};
  }
}

// Вызывается при загрузке сайта. Новый рекламный переход в той же вкладке
// перекрывает прежний (это более свежий источник); заход без меток
// сохранённое не трогает.
export function captureUtmFromUrl() {
  if (typeof window === "undefined") {
    return;
  }

  const fromUrl = readUtmFromUrl();
  if (Object.keys(fromUrl).length === 0) {
    return;
  }

  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(fromUrl));
  } catch {
    // Хранилище недоступно — метки останутся только в адресе, как раньше.
  }
}

// Если в адресе есть хоть одна метка — берём набор из адреса, иначе
// сохранённый при входе. Набор всегда из одного источника, чтобы не склеить
// в одной заявке метки двух разных переходов.
export function getUtmValue(key: UtmKey): string {
  if (typeof window === "undefined") {
    return "";
  }

  const fromUrl = readUtmFromUrl();
  const source = Object.keys(fromUrl).length > 0 ? fromUrl : readStoredUtm();
  return source[key] ?? "";
}
