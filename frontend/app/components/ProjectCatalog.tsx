"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import CatalogFilterPanel, {
  EMPTY_FILTERS,
  Filters,
  FilterGroupKey,
  ProjectCategory,
  getActiveFilterChips,
} from "./CatalogFilterPanel";
import filterPanelStyles from "./CatalogFilterPanel.module.css";
import CustomProjectCard from "./CustomProjectCard";

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

function buildProjectsUrl(
  filters: Filters,
  page = 1,
  ordering: Ordering = "default",
  paginate = true,
  lockedSize?: { width?: number; length?: number },
  pageSize: number = PAGE_SIZE,
) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
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

  if (ordering !== "default") {
    params.set("ordering", ordering);
  }
  if (paginate) {
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
  }

  const query = params.toString();

  return query ? `${apiUrl}/projects/?${query}` : `${apiUrl}/projects/`;
}

export default function ProjectCatalog({
  initialCategory = "",
  showCategoryFilter = true,
  showFilters = true,
  maxItems,
  eyebrow = "Каталог",
  title = "Популярные проекты",
  description = "Выберите готовый проект или отправьте свой — менеджер поможет рассчитать стоимость под нужную комплектацию.",
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
  const [previewCount, setPreviewCount] = useState<number | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isMobileFiltersOpen, setIsMobileFiltersOpen] = useState(false);
  const [ordering, setOrdering] = useState<Ordering>("default");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProjects, setTotalProjects] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const usesPagination = !maxItems;

  function applyProjectsResponse(data: Project[] | PaginatedProjects) {
    if (Array.isArray(data)) {
      setProjects(data);
      setTotalProjects(data.length);
      return;
    }
    setProjects(data.results);
    setTotalProjects(data.count);
  }

  function updateBrowserPage(page: number) {
    if (!usesPagination || typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (page > 1) {
      url.searchParams.set("page", String(page));
    } else {
      url.searchParams.delete("page");
    }
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
      updateBrowserPage(nextPage);
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

  useEffect(() => {
    let isCancelled = false;

    async function initialLoad() {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const pageFromUrl = usesPagination
        ? Math.max(
            1,
            Number(new URLSearchParams(window.location.search).get("page")) || 1
          )
        : 1;

      try {
        const [categoriesResponse, projectsResponse] = await Promise.all([
          fetch(`${apiUrl}/categories/`),
          fetch(
            buildProjectsUrl(
              initialFilters,
              pageFromUrl,
              "default",
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

  // Живой счётчик "Показать N проектов" на кнопке фильтров: считает, сколько
  // проектов подойдёт под ЕЩЁ НЕ применённые (staged) фильтры. Отдельный
  // облегчённый запрос с page_size=1 — нужен только заголовок count из
  // пагинации, сам список результатов не используется.
  useEffect(() => {
    if (!showFilters) return;

    let isCancelled = false;
    const timer = setTimeout(async () => {
      setIsPreviewLoading(true);
      try {
        const response = await fetch(
          buildProjectsUrl(filters, 1, "default", true, lockedSize, 1)
        );
        if (!response.ok) throw new Error();
        const data = (await response.json()) as PaginatedProjects;
        if (!isCancelled) {
          setPreviewCount(typeof data.count === "number" ? data.count : null);
        }
      } catch {
        if (!isCancelled) setPreviewCount(null);
      } finally {
        if (!isCancelled) setIsPreviewLoading(false);
      }
    }, 400);

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

  const activeChips = getActiveFilterChips(appliedFilters);

  return (
    <section className="container section catalogSection" id="projects">
      <div className="sectionHeader sectionHeaderRow">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>

      <div className={showFilters ? "catalogLayout" : "catalogLayout catalogLayoutPlain"}>
        {showFilters && (
          <CatalogFilterPanel
            categories={categories}
            showCategoryFilter={showCategoryFilter}
            filters={filters}
            previewCount={previewCount}
            isPreviewLoading={isPreviewLoading}
            isMobileOpen={isMobileFiltersOpen}
            onCloseMobile={() => setIsMobileFiltersOpen(false)}
            onUpdateFilter={updateFilter}
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
                    <span>Сортировка</span>
                    <select
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
                <article className="projectCard" key={project.id}>
                  <Link className="projectImage" href={`/projects/${project.slug}`}>
                    {project.main_image ? (
                      <Image
                        src={project.main_image}
                        alt={project.title}
                        fill
                        sizes="(max-width: 680px) 100vw, (max-width: 1100px) 50vw, 33vw"
                        style={{ objectFit: "cover" }}
                      />
                    ) : (
                      <div className="imagePlaceholder">Фото проекта</div>
                    )}

                    <span className="projectBadge">{project.category.title}</span>
                  </Link>

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
                      <Link href={`/projects/${project.slug}`}>Подробнее</Link>
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
    </section>
  );
}
