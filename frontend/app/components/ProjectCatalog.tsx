"use client";

import Link from "next/link";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import CatalogFilterPanel, {
  CatalogFacets,
  EMPTY_FILTERS,
  Filters,
  FilterGroupKey,
  ProjectCategory,
  RangeFilterKey,
  getActiveFilterChips,
} from "./CatalogFilterPanel";
import filterPanelStyles from "./CatalogFilterPanel.module.css";
import { useCardPeek } from "../lib/useCardPeek";
import CardPeekPreview from "./CardPeekPreview";
import peekStyles from "./CardPeekPreview.module.css";
import CustomProjectCard from "./CustomProjectCard";
import ProjectCardMedia from "./ProjectCardMedia";

type Project = {
  id: number;
  external_id: string | null;
  title: string;
  slug: string;
  category: ProjectCategory;
  area: string | number | null;
  floor_label: string;
  size_text: string;
  price_from: string | number | null;
  short_description: string;
  main_image: string | null;
  // Необязательное: старый бэкенд поле не отдаёт — тогда в карточке просто
  // одна обложка, как раньше.
  plan_images?: string[];
};

type Ordering =
  | "default"
  | "newest"
  | "price_asc"
  | "price_desc"
  | "area_asc"
  | "area_desc"
  | "title";

type PaginatedProjects = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Project[];
};

type LockedSize = { width?: number; length?: number };

type ProjectCatalogProps = {
  initialCategory?: string;
  showCategoryFilter?: boolean;
  showFilters?: boolean;
  maxItems?: number;
  eyebrow?: string;
  title?: string;
  description?: string;
  moreHref?: string;
  moreLabel?: string;
  // Карточка "Свой проект" — предложение прислать эскиз/фото. Нужна на
  // страницах каталога (/doma-iz-brusa, /bani-iz-brusa), но не в мини-подборке
  // на главной — там уже есть отдельная карточка "Индивидуальный проект" в
  // блоке "Выберите направление" чуть выше, повторять предложение не нужно.
  showCustomProjectCard?: boolean;
  // Жёсткое ограничение по размеру footprint (например, для страницы
  // "Дома из бруса 6х6"). В отличие от Filters, это не пользовательский
  // фильтр — оно задаётся страницей и всегда применяется поверх остальных
  // условий, включая сброс фильтров и переключение сортировки/страниц.
  filterWidth?: number;
  filterLength?: number;
};

function formatPrice(price: string | number | null) {
  if (!price) {
    return "Цена по запросу";
  }

  const numericPrice = Number(price);

  if (Number.isNaN(numericPrice)) {
    return "Цена по запросу";
  }

  return `от ${numericPrice.toLocaleString("ru-RU")} ₽`;
}

const PAGE_SIZE = 20;

const orderingOptions: { value: Ordering; label: string }[] = [
  { value: "default", label: "По популярности" },
  { value: "newest", label: "Сначала новые" },
  { value: "price_asc", label: "Сначала дешевле" },
  { value: "price_desc", label: "Сначала дороже" },
  { value: "area_asc", label: "Площадь: по возрастанию" },
  { value: "area_desc", label: "Площадь: по убыванию" },
  { value: "title", label: "По названию" },
];

// Параметры отбора — общие для списка проектов и для счётчиков в панели
// фильтров (/projects/facets/), чтобы цифра на кнопке совпадала с выдачей.
function buildFilterParams(filters: Filters, lockedSize?: LockedSize) {
  const params = new URLSearchParams();

  if (filters.category) params.set("category", filters.category);
  if (filters.construction_types.length) {
    params.set("construction_type", filters.construction_types.join(","));
  }
  if (filters.floors_list.length) {
    params.set("floors", filters.floors_list.join(","));
  }
  if (filters.materials.length) {
    params.set("material", filters.materials.join(","));
  }
  if (filters.size_min) params.set("size_min", filters.size_min);
  if (filters.size_max) params.set("size_max", filters.size_max);
  if (filters.area_min) params.set("area_min", filters.area_min);
  if (filters.area_max) params.set("area_max", filters.area_max);
  if (filters.price_min) params.set("price_min", filters.price_min);
  if (filters.price_max) params.set("price_max", filters.price_max);

  if (lockedSize?.width) {
    params.set("width", String(lockedSize.width));
  }
  if (lockedSize?.length) {
    params.set("length", String(lockedSize.length));
  }

  return params;
}

function withQuery(path: string, params: URLSearchParams) {
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

function buildProjectsUrl(
  filters: Filters,
  page = 1,
  ordering: Ordering = "default",
  paginate = true,
  lockedSize?: LockedSize,
) {
  const params = buildFilterParams(filters, lockedSize);

  if (ordering !== "default") {
    params.set("ordering", ordering);
  }
  if (paginate) {
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));
  }

  return withQuery(`${process.env.NEXT_PUBLIC_API_URL}/projects/`, params);
}

function buildFacetsUrl(filters: Filters, lockedSize?: LockedSize) {
  return withQuery(
    `${process.env.NEXT_PUBLIC_API_URL}/projects/facets/`,
    buildFilterParams(filters, lockedSize),
  );
}

// --- Фильтры в адресной строке -------------------------------------------
//
// Нужно, чтобы отфильтрованную выборку можно было переслать, положить в
// закладки и вернуться к ней кнопкой "Назад", а также чтобы вести рекламу
// сразу на нужный срез каталога без отдельной посадочной страницы.
//
// Для SEO это НЕ плюс: фасетная навигация плодит тысячи почти одинаковых
// адресов. Защита — canonical на чистый адрес страницы (см. metadata в
// app/[slug]/page.tsx) плюс Clean-param в robots.txt.
//
// Списки пишем через запятую (значения — латинские слаги, запятых внутри
// нет), но при чтении принимаем и повторяющиеся параметры вида
// ?type=timber&type=frame — так URL переживёт ручную правку.

// Ключи адреса, которыми управляет каталог. Всё остальное в query (utm_*,
// yclid и прочие параметры рекламы) syncBrowserUrl обязан оставлять
// нетронутым. Список должен совпадать с Clean-param в app/robots.txt.
const CATALOG_URL_KEYS = [
  "category",
  "type",
  "floors",
  "material",
  "size_min",
  "size_max",
  "area_min",
  "area_max",
  "price_min",
  "price_max",
  "ordering",
  "page",
] as const;

// Раньше материал в адресе был типом бруса (profiled и т. п.), теперь это
// группа материалов из базы (catalog/filters.py → material_group_value).
// Старые ссылки переводим на новые значения.
const LEGACY_MATERIAL_VALUES: Record<string, string> = {
  regular: "obychnyy-brus",
  profiled: "profilirovannyy-brus",
  dry: "brus-kamernoy-sushki",
};

function filtersToSearchParams(
  filters: Filters,
  ordering: Ordering,
  page: number,
  initialCategory: string,
) {
  const params = new URLSearchParams();

  // Категорию пишем, только если пользователь сменил её сам: на странице
  // категории она задана самим адресом, дублировать её в query незачем.
  if (filters.category && filters.category !== initialCategory) {
    params.set("category", filters.category);
  }
  if (filters.construction_types.length) {
    params.set("type", filters.construction_types.join(","));
  }
  if (filters.floors_list.length) {
    params.set("floors", filters.floors_list.join(","));
  }
  if (filters.materials.length) {
    params.set("material", filters.materials.join(","));
  }
  if (filters.size_min) params.set("size_min", filters.size_min);
  if (filters.size_max) params.set("size_max", filters.size_max);
  if (filters.area_min) params.set("area_min", filters.area_min);
  if (filters.area_max) params.set("area_max", filters.area_max);
  if (filters.price_min) params.set("price_min", filters.price_min);
  if (filters.price_max) params.set("price_max", filters.price_max);

  if (ordering !== "default") params.set("ordering", ordering);
  if (page > 1) params.set("page", String(page));

  return params;
}

function filtersFromSearchParams(search: string, initialCategory: string) {
  const params = new URLSearchParams(search);
  const readList = (key: string) =>
    params
      .getAll(key)
      .flatMap((value) => value.split(","))
      .map((value) => value.trim())
      .filter(Boolean);

  const filters: Filters = {
    category: params.get("category") || initialCategory,
    // Значения, которых нет среди проектов (например, ?type=frame по старой
    // ссылке), бэкенд всё равно вернёт в вариантах панели — галочку можно
    // снять, пустой каталог не «застревает».
    construction_types: readList("type"),
    floors_list: readList("floors"),
    materials: Array.from(
      new Set(
        readList("material").map(
          (value) => LEGACY_MATERIAL_VALUES[value] ?? value,
        ),
      ),
    ),
    size_min: params.get("size_min") || "",
    size_max: params.get("size_max") || "",
    area_min: params.get("area_min") || "",
    area_max: params.get("area_max") || "",
    price_min: params.get("price_min") || "",
    price_max: params.get("price_max") || "",
  };

  const orderingParam = params.get("ordering") || "";
  const ordering: Ordering = orderingOptions.some(
    (option) => option.value === orderingParam,
  )
    ? (orderingParam as Ordering)
    : "default";

  return {
    filters,
    ordering,
    page: Math.max(1, Number(params.get("page")) || 1),
  };
}

// --- Возврат к каталогу кнопкой «Назад» ----------------------------------
//
// Проекты каталог грузит уже в браузере. Раньше после «Назад» страница
// открывалась с «Загружаем проекты…», браузеру было некуда вернуть прокрутку,
// и человек оказывался не там, где был. Теперь последний показанный список и
// позиция прокрутки лежат в sessionStorage по адресу страницы: при возврате
// по истории (или обновлении страницы) каталог сразу рисует тот же список и
// встаёт на то же место, а свежие данные подтягиваются в фоне.

type CatalogView = {
  projects: Project[];
  totalProjects: number;
  currentPage: number;
  filters: Filters;
  ordering: Ordering;
};

type CatalogViewSnapshot = CatalogView & {
  scrollY: number;
  savedAt: number;
};

const VIEW_SNAPSHOT_PREFIX = "catalog-view:";
const VIEW_SNAPSHOT_TTL_MS = 30 * 60 * 1000;
// Сколько после popstate ждём монтирования каталога, чтобы считать это
// возвратом по истории, а не обычным переходом по ссылке.
const HISTORY_RETURN_WINDOW_MS = 5000;

let lastPopStateAt = 0;
let isFirstCatalogMount = true;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    lastPopStateAt = Date.now();
  });
}

function currentViewKey() {
  return `${VIEW_SNAPSHOT_PREFIX}${window.location.pathname}${window.location.search}`;
}

function readViewSnapshot(key: string): CatalogViewSnapshot | null {
  try {
    const raw = window.sessionStorage.getItem(key);
    if (!raw) return null;

    const snapshot = JSON.parse(raw) as CatalogViewSnapshot;
    if (
      !Array.isArray(snapshot.projects) ||
      Date.now() - snapshot.savedAt > VIEW_SNAPSHOT_TTL_MS
    ) {
      return null;
    }
    return snapshot;
  } catch {
    return null;
  }
}

function writeViewSnapshot(key: string, view: CatalogView, scrollY: number) {
  try {
    const snapshot: CatalogViewSnapshot = { ...view, scrollY, savedAt: Date.now() };
    window.sessionStorage.setItem(key, JSON.stringify(snapshot));
  } catch {
    // Приватный режим или переполненное хранилище — позицию просто не вернём.
  }
}

function scrollInstantly(top: number) {
  // У html плавная прокрутка (globals.css) — возврат на место должен быть
  // мгновенным, без «отмотки».
  const html = document.documentElement;
  const previousScrollBehavior = html.style.scrollBehavior;
  html.style.scrollBehavior = "auto";
  window.scrollTo(0, top);
  html.style.scrollBehavior = previousScrollBehavior;
}

export default function ProjectCatalog({
  initialCategory = "",
  showCategoryFilter = true,
  showFilters = true,
  maxItems,
  eyebrow = "Каталог",
  title = "Популярные проекты",
  description = "",
  moreHref,
  moreLabel = "Смотреть больше",
  filterWidth,
  filterLength,
  showCustomProjectCard = true,
}: ProjectCatalogProps) {
  const lockedSize =
    filterWidth || filterLength
      ? { width: filterWidth, length: filterLength }
      : undefined;

  const initialFilters: Filters = {
    category: initialCategory,
    ...EMPTY_FILTERS,
  };

  const [categories, setCategories] = useState<ProjectCategory[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [appliedFilters, setAppliedFilters] = useState<Filters>(initialFilters);
  const [facets, setFacets] = useState<CatalogFacets | null>(null);
  const [isFacetsLoading, setIsFacetsLoading] = useState(false);
  const [isMobileFiltersOpen, setIsMobileFiltersOpen] = useState(false);
  const [ordering, setOrdering] = useState<Ordering>("default");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProjects, setTotalProjects] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [restoreScrollY, setRestoreScrollY] = useState<number | null>(null);
  const { peek, bindCard } = useCardPeek();

  const scrollYRef = useRef(0);
  const viewRef = useRef<{ key: string; view: CatalogView } | null>(null);

  const usesPagination = !maxItems;

  function persistView() {
    const entry = viewRef.current;
    if (entry) writeViewSnapshot(entry.key, entry.view, scrollYRef.current);
  }

  function applyProjectsResponse(data: Project[] | PaginatedProjects) {
    if (Array.isArray(data)) {
      setProjects(data);
      setTotalProjects(data.length);
      return;
    }
    setProjects(data.results);
    setTotalProjects(data.count);
  }

  function syncBrowserUrl(
    nextFilters: Filters,
    page: number,
    nextOrdering: Ordering,
  ) {
    if (!usesPagination || typeof window === "undefined") return;

    const url = new URL(window.location.href);

    // На размерной странице (/doma-iz-brusa-6x6) размер задан самим слагом,
    // и писать фильтры в query нельзя: получился бы адрес, который сам себе
    // противоречит. Там по-прежнему синхронизируем только страницу.
    if (lockedSize) {
      if (page > 1) {
        url.searchParams.set("page", String(page));
      } else {
        url.searchParams.delete("page");
      }
      window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
      return;
    }

    // Меняем только свои ключи. Раньше адрес пересобирался из одних
    // фильтров, и стоило посетителю с рекламы тронуть фильтр или сортировку,
    // как utm_* и yclid из адреса пропадали — а вместе с ними и источник
    // заявки.
    for (const key of CATALOG_URL_KEYS) {
      url.searchParams.delete(key);
    }
    filtersToSearchParams(
      nextFilters,
      nextOrdering,
      page,
      initialCategory,
    ).forEach((value, key) => {
      url.searchParams.set(key, value);
    });

    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  }

  async function loadProjects(
    nextFilters: Filters,
    nextPage = 1,
    nextOrdering: Ordering = ordering,
  ) {
    setIsLoading(true);
    setErrorMessage("");
    setAppliedFilters(nextFilters);

    try {
      const response = await fetch(
        buildProjectsUrl(
          nextFilters,
          nextPage,
          nextOrdering,
          usesPagination,
          lockedSize,
        )
      );

      if (!response.ok) {
        throw new Error("Не удалось загрузить проекты");
      }

      const data = (await response.json()) as Project[] | PaginatedProjects;
      applyProjectsResponse(data);
      setCurrentPage(nextPage);
      syncBrowserUrl(nextFilters, nextPage, nextOrdering);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Произошла ошибка при загрузке каталога"
      );
    } finally {
      setIsLoading(false);
    }
  }

  function updateFilter<K extends keyof Filters>(field: K, value: Filters[K]) {
    setFilters((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function updateRange(field: RangeFilterKey, min: string, max: string) {
    setFilters((current) => {
      const next = { ...current };
      next[`${field}_min` as const] = min;
      next[`${field}_max` as const] = max;
      return next;
    });
  }

  function toggleListFilter(
    field: "construction_types" | "floors_list" | "materials",
    value: string,
  ) {
    setFilters((current) => {
      const list = current[field];
      const nextList = list.includes(value)
        ? list.filter((item) => item !== value)
        : [...list, value];
      return { ...current, [field]: nextList };
    });
  }

  function handleFilterSubmit() {
    loadProjects(filters, 1);
  }

  function resetFilters() {
    const resetValues: Filters = {
      category: initialCategory,
      ...EMPTY_FILTERS,
    };

    setFilters(resetValues);
    setOrdering("default");
    loadProjects(resetValues, 1, "default");
  }

  function removeFilterGroup(group: FilterGroupKey) {
    const next: Filters = { ...filters };

    if (group === "construction_types") next.construction_types = [];
    else if (group === "floors_list") next.floors_list = [];
    else if (group === "materials") next.materials = [];
    else if (group === "size") {
      next.size_min = "";
      next.size_max = "";
    } else if (group === "area") {
      next.area_min = "";
      next.area_max = "";
    } else if (group === "price") {
      next.price_min = "";
      next.price_max = "";
    }

    setFilters(next);
    loadProjects(next, 1);
  }

  function handleOrderingChange(value: Ordering) {
    setOrdering(value);
    loadProjects(filters, 1, value);
  }

  function changePage(nextPage: number) {
    if (nextPage === currentPage || nextPage < 1) return;
    loadProjects(filters, nextPage);
    document.getElementById("projects")?.scrollIntoView({ behavior: "smooth" });
  }

  // Возврат по истории: сразу показываем прошлый список (до отрисовки, чтобы
  // не мелькало «Загружаем проекты…») и встаём на прошлое место прокрутки.
  useLayoutEffect(() => {
    const firstMount = isFirstCatalogMount;
    isFirstCatalogMount = false;

    const navigation = window.performance?.getEntriesByType?.("navigation")[0] as
      | PerformanceNavigationTiming
      | undefined;
    const returnedByHistory =
      Date.now() - lastPopStateAt < HISTORY_RETURN_WINDOW_MS ||
      (firstMount &&
        (navigation?.type === "back_forward" || navigation?.type === "reload"));
    if (!returnedByHistory) return;

    const snapshot = readViewSnapshot(currentViewKey());
    if (!snapshot) return;

    /* eslint-disable react-hooks/set-state-in-effect -- восстановление
       прошлого вида должно попасть в тот же кадр, до отрисовки */
    setProjects(snapshot.projects);
    setTotalProjects(snapshot.totalProjects);
    setCurrentPage(snapshot.currentPage);
    setFilters(snapshot.filters);
    setAppliedFilters(snapshot.filters);
    setOrdering(snapshot.ordering);
    setIsLoading(false);
    setRestoreScrollY(snapshot.scrollY);
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  useLayoutEffect(() => {
    if (restoreScrollY === null) return;

    scrollInstantly(restoreScrollY);
    scrollYRef.current = restoreScrollY;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- одноразовый флаг
    setRestoreScrollY(null);
  }, [restoreScrollY]);

  // Запоминаем показанный список — для возврата «Назад».
  useEffect(() => {
    if (isLoading || errorMessage) return;

    viewRef.current = {
      key: currentViewKey(),
      view: {
        projects: maxItems ? projects.slice(0, maxItems) : projects,
        totalProjects,
        currentPage,
        filters: appliedFilters,
        ordering,
      },
    };
    persistView();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projects, totalProjects, currentPage, appliedFilters, ordering, isLoading, errorMessage]);

  useEffect(() => {
    let saveTimer = 0;

    function handleScroll() {
      scrollYRef.current = window.scrollY;
      window.clearTimeout(saveTimer);
      saveTimer = window.setTimeout(persistView, 250);
    }

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      window.clearTimeout(saveTimer);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  // Уход со страницы (например, клик по проекту): позицию сохраняем до того,
  // как Next прокрутит новую страницу к началу.
  useLayoutEffect(() => {
    return () => persistView();
  }, []);

  useEffect(() => {
    let isCancelled = false;

    async function initialLoad() {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;

      // Восстанавливаем состояние из адреса: человек мог прийти по
      // пересланной ссылке, нажать "Назад" или просто обновить страницу.
      // На размерных страницах фильтры в адрес не пишутся (см.
      // syncBrowserUrl), поэтому там читаем только номер страницы.
      const fromUrl =
        usesPagination && !lockedSize
          ? filtersFromSearchParams(window.location.search, initialCategory)
          : null;

      const startFilters = fromUrl?.filters ?? initialFilters;
      const startOrdering: Ordering = fromUrl?.ordering ?? "default";
      const pageFromUrl = usesPagination
        ? fromUrl?.page ??
          Math.max(
            1,
            Number(new URLSearchParams(window.location.search).get("page")) || 1
          )
        : 1;

      try {
        const [categoriesResponse, projectsResponse] = await Promise.all([
          fetch(`${apiUrl}/categories/`),
          fetch(
            buildProjectsUrl(
              startFilters,
              pageFromUrl,
              startOrdering,
              usesPagination,
              lockedSize
            )
          ),
        ]);

        if (!projectsResponse.ok) {
          throw new Error("Не удалось загрузить проекты");
        }

        const categoriesData = categoriesResponse.ok
          ? await categoriesResponse.json()
          : [];

        const projectsData = (await projectsResponse.json()) as
          | Project[]
          | PaginatedProjects;

        if (!isCancelled) {
          setCategories(categoriesData);
          applyProjectsResponse(projectsData);
          setCurrentPage(pageFromUrl);
          // Панель фильтров и чипсы должны показывать то же, что в адресе.
          setFilters(startFilters);
          setAppliedFilters(startFilters);
          setOrdering(startOrdering);
        }
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Произошла ошибка при загрузке каталога"
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    initialLoad();

    return () => {
      isCancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Варианты фильтров и цифры напротив них для ЕЩЁ НЕ применённых (staged)
  // фильтров: пересчитываются при каждом изменении в панели, число на кнопке
  // «Показать N проектов» — оттуда же.
  useEffect(() => {
    if (!showFilters) return;

    let isCancelled = false;
    const timer = setTimeout(async () => {
      setIsFacetsLoading(true);
      try {
        const response = await fetch(buildFacetsUrl(filters, lockedSize));
        if (!response.ok) throw new Error();
        const data = (await response.json()) as CatalogFacets;
        if (!isCancelled) setFacets(data);
      } catch {
        // Панель остаётся с прошлыми цифрами — отбирать проекты это не мешает.
      } finally {
        if (!isCancelled) setIsFacetsLoading(false);
      }
    }, 250);

    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, showFilters]);

  const visibleProjects = maxItems ? projects.slice(0, maxItems) : projects;
  const totalPages = usesPagination
    ? Math.max(1, Math.ceil(totalProjects / PAGE_SIZE))
    : 1;
  const pageNumbers = Array.from({ length: totalPages }, (_, index) => index + 1)
    .filter(
      (pageNumber) =>
        pageNumber === 1 ||
        pageNumber === totalPages ||
        Math.abs(pageNumber - currentPage) <= 2
    );

  const activeChips = getActiveFilterChips(appliedFilters, facets);

  return (
    <section className="container section catalogSection" id="projects">
      <div className="sectionHeader sectionHeaderRow">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
      </div>

      <div className={showFilters ? "catalogLayout" : "catalogLayout catalogLayoutPlain"}>
        {showFilters && (
          <CatalogFilterPanel
            categories={categories}
            showCategoryFilter={showCategoryFilter}
            filters={filters}
            facets={facets}
            isFacetsLoading={isFacetsLoading}
            isMobileOpen={isMobileFiltersOpen}
            onCloseMobile={() => setIsMobileFiltersOpen(false)}
            onUpdateFilter={updateFilter}
            onUpdateRange={updateRange}
            onToggleListFilter={toggleListFilter}
            onSubmit={handleFilterSubmit}
            onReset={resetFilters}
          />
        )}

        <div className="catalogContent">
          {!isLoading && !errorMessage && (
            <>
              {showFilters && activeChips.length > 0 && (
                <div className={filterPanelStyles.chipsRow}>
                  {activeChips.map((chip) => (
                    <button
                      type="button"
                      className={filterPanelStyles.chip}
                      key={chip.key}
                      onClick={() => removeFilterGroup(chip.key)}
                    >
                      {chip.label}
                      <span aria-hidden="true">×</span>
                    </button>
                  ))}
                  <button
                    type="button"
                    className={filterPanelStyles.chipReset}
                    onClick={resetFilters}
                  >
                    Сбросить все
                  </button>
                </div>
              )}

              <div className="catalogToolbar">
                <span className={filterPanelStyles.toolbarCount}>
                  Найдено проектов: <strong>{totalProjects}</strong>
                </span>

                <div className={filterPanelStyles.toolbarControls}>
                  {showFilters && (
                    <button
                      type="button"
                      className={filterPanelStyles.mobileTrigger}
                      onClick={() => setIsMobileFiltersOpen(true)}
                    >
                      <svg viewBox="0 0 20 20" aria-hidden="true">
                        <path d="M3 5h14M6 10h8M8.5 15h3" />
                      </svg>
                      Фильтры{activeChips.length > 0 ? ` · ${activeChips.length}` : ""}
                    </button>
                  )}

                  <label>
                    <span className={filterPanelStyles.sortCaption}>Сортировка</span>
                    <select
                      className={filterPanelStyles.sortSelect}
                      aria-label="Сортировка проектов"
                      value={ordering}
                      onChange={(event) =>
                        handleOrderingChange(event.target.value as Ordering)
                      }
                    >
                      {orderingOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
            </>
          )}
          {isLoading && <div className="catalogState">Загружаем проекты...</div>}

          {errorMessage && <div className="catalogError">{errorMessage}</div>}

          {!isLoading && !errorMessage && visibleProjects.length === 0 && (
            <div className="catalogState">
              По выбранным параметрам проекты не найдены. Попробуйте изменить
              фильтры.
            </div>
          )}

          {!isLoading &&
            (visibleProjects.length > 0 ||
              (showCustomProjectCard && currentPage === 1)) && (
            <div className="projectGrid">
              {showCustomProjectCard && currentPage === 1 && (
                <CustomProjectCard />
              )}
              {visibleProjects.map((project) => (
                <article
                  className={`projectCard ${peekStyles.peekable}`}
                  key={project.id}
                  {...bindCard(project.title)}
                >
                  <ProjectCardMedia
                    href={`/projects/${project.slug}`}
                    title={project.title}
                    badge={project.category.title}
                    mainImage={project.main_image}
                    planImages={project.plan_images}
                    sizes="(max-width: 680px) 100vw, (max-width: 1100px) 50vw, 33vw"
                  />

                  <div className="projectBody">
                    <div className="projectTop">
                      <span>{project.size_text || "Размер уточняется"}</span>
                      {project.area && <span>{project.area} м²</span>}
                    </div>

                    <h3>{project.title}</h3>

                    <p>
                      {project.short_description ||
                        "Описание проекта скоро появится."}
                    </p>

                    <div className="projectSpecs">
                      {project.floor_label && <span>{project.floor_label}</span>}
                      {project.external_id && <span>{project.external_id}</span>}
                    </div>

                    <div className="projectFooter">
                      <strong>{formatPrice(project.price_from)}</strong>
                      <Link href={`/projects/${project.slug}`} draggable={false}>
                        Подробнее
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {!isLoading && !errorMessage && totalPages > 1 && (
            <nav className="catalogPagination" aria-label="Страницы каталога">
              <button
                disabled={currentPage === 1}
                onClick={() => changePage(currentPage - 1)}
                type="button"
              >
                ← Назад
              </button>

              <div>
                {pageNumbers.map((pageNumber, index) => {
                  const previousNumber = pageNumbers[index - 1];
                  return (
                    <span key={pageNumber}>
                      {previousNumber && pageNumber - previousNumber > 1 && (
                        <i>…</i>
                      )}
                      <button
                        aria-current={pageNumber === currentPage ? "page" : undefined}
                        className={pageNumber === currentPage ? "isActive" : ""}
                        onClick={() => changePage(pageNumber)}
                        type="button"
                      >
                        {pageNumber}
                      </button>
                    </span>
                  );
                })}
              </div>

              <button
                disabled={currentPage === totalPages}
                onClick={() => changePage(currentPage + 1)}
                type="button"
              >
                Вперёд →
              </button>
            </nav>
          )}
        </div>
      </div>
      {moreHref && !isLoading && visibleProjects.length > 0 && (
        <div className="catalogMore">
            <Link className="buttonPrimary" href={moreHref}>
            {moreLabel}
            </Link>
        </div>
        )}
      <CardPeekPreview peek={peek} />
    </section>
  );
}
