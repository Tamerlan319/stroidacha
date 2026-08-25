"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

type ProjectCategory = {
  id: number;
  title: string;
  slug: string;
};

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

type Filters = {
  category: string;
  construction_type: string;
  area_min: string;
  area_max: string;
  price_max: string;
  floors: string;
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
  // Жёсткое ограничение по размеру footprint (например, для страницы
  // "Дома из бруса 6х6"). В отличие от Filters, это не пользовательский
  // фильтр — оно задаётся страницей и всегда применяется поверх остальных
  // условий, включая сброс фильтров и переключение сортировки/страниц.
  filterWidth?: number;
  filterLength?: number;
};

const constructionTypes = [
  { value: "", label: "Любой тип" },
  { value: "timber", label: "Брус" },
  { value: "frame", label: "Каркас" },
  { value: "log", label: "Бревно" },
  { value: "other", label: "Другое" },
];

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
) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });

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
    params.set("page_size", String(PAGE_SIZE));
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
}: ProjectCatalogProps) {
  const lockedSize =
    filterWidth || filterLength
      ? { width: filterWidth, length: filterLength }
      : undefined;

  const initialFilters: Filters = {
    category: initialCategory,
    construction_type: "",
    area_min: "",
    area_max: "",
    price_max: "",
    floors: "",
  };

  const [categories, setCategories] = useState<ProjectCategory[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [filters, setFilters] = useState<Filters>(initialFilters);
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

  function updateFilter(field: keyof Filters, value: string) {
    setFilters((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadProjects(filters, 1);
  }

  function resetFilters() {
    const resetValues: Filters = {
      category: initialCategory,
      construction_type: "",
      area_min: "",
      area_max: "",
      price_max: "",
      floors: "",
    };

    setFilters(resetValues);
    setOrdering("default");
    loadProjects(resetValues, 1, "default");
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
          <aside className="catalogSidebar">
            <div className="catalogSidebarTitle">
              <strong>Подбор проекта</strong>
              <span>Настройте параметры</span>
            </div>

            <form className="catalogFilters" onSubmit={handleSubmit}>
              {showCategoryFilter && (
                <label>
                  <span>Категория</span>
                  <select
                    value={filters.category}
                    onChange={(event) => updateFilter("category", event.target.value)}
                  >
                    <option value="">Все категории</option>

                    {categories.map((category) => (
                      <option value={category.slug} key={category.id}>
                        {category.title}
                      </option>
                    ))}
                  </select>
                </label>
              )}

              <label>
                <span>Тип</span>
                <select
                  value={filters.construction_type}
                  onChange={(event) =>
                    updateFilter("construction_type", event.target.value)
                  }
                >
                  {constructionTypes.map((type) => (
                    <option value={type.value} key={type.value || "all"}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>Площадь от, м²</span>
                <input
                  type="number"
                  min="0"
                  value={filters.area_min}
                  onChange={(event) => updateFilter("area_min", event.target.value)}
                  placeholder="40"
                />
              </label>

              <label>
                <span>Площадь до, м²</span>
                <input
                  type="number"
                  min="0"
                  value={filters.area_max}
                  onChange={(event) => updateFilter("area_max", event.target.value)}
                  placeholder="120"
                />
              </label>

              <label>
                <span>Цена до, ₽</span>
                <input
                  type="number"
                  min="0"
                  value={filters.price_max}
                  onChange={(event) => updateFilter("price_max", event.target.value)}
                  placeholder="1500000"
                />
              </label>

              <label>
                <span>Этажность</span>
                <select
                  value={filters.floors}
                  onChange={(event) => updateFilter("floors", event.target.value)}
                >
                  <option value="">Любая</option>
                  <option value="1">1 этаж</option>
                  <option value="1.5">1,5 этажа</option>
                  <option value="2">2 этажа</option>
                </select>
              </label>

              <div className="filterActions">
                <button className="buttonPrimary" type="submit">
                  Показать
                </button>

                <button
                  className="buttonGhost"
                  type="button"
                  onClick={resetFilters}
                >
                  Сбросить фильтры
                </button>
              </div>
            </form>
          </aside>
        )}

        <div className="catalogContent">
          {!isLoading && !errorMessage && (
            <div className="catalogToolbar">
              <span>
                Найдено проектов: <strong>{totalProjects}</strong>
              </span>
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
          )}
          {isLoading && <div className="catalogState">Загружаем проекты...</div>}

          {errorMessage && <div className="catalogError">{errorMessage}</div>}

          {!isLoading && !errorMessage && visibleProjects.length === 0 && (
            <div className="catalogState">
              По выбранным параметрам проекты не найдены. Попробуйте изменить
              фильтры.
            </div>
          )}

          {!isLoading && visibleProjects.length > 0 && (
            <div className="projectGrid">
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
