"use client";

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
};

type ProjectCatalogProps = {
  initialCategory?: string;
  showCategoryFilter?: boolean;
  showFilters?: boolean;
  maxItems?: number;
  eyebrow?: string;
  title?: string;
  description?: string;
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

function buildProjectsUrl(filters: Filters) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });

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
}: ProjectCatalogProps) {
  const initialFilters: Filters = {
    category: initialCategory,
    construction_type: "",
    area_min: "",
    area_max: "",
    price_max: "",
  };

  const [categories, setCategories] = useState<ProjectCategory[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadProjects(nextFilters: Filters) {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch(buildProjectsUrl(nextFilters));

      if (!response.ok) {
        throw new Error("Не удалось загрузить проекты");
      }

      const data = await response.json();
      setProjects(data);
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
    loadProjects(filters);
  }

  function resetFilters() {
    const resetValues: Filters = {
      category: initialCategory,
      construction_type: "",
      area_min: "",
      area_max: "",
      price_max: "",
    };

    setFilters(resetValues);
    loadProjects(resetValues);
  }

  useEffect(() => {
    let isCancelled = false;

    async function initialLoad() {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;

      try {
        const [categoriesResponse, projectsResponse] = await Promise.all([
          fetch(`${apiUrl}/categories/`),
          fetch(buildProjectsUrl(initialFilters)),
        ]);

        if (!projectsResponse.ok) {
          throw new Error("Не удалось загрузить проекты");
        }

        const categoriesData = categoriesResponse.ok
          ? await categoriesResponse.json()
          : [];

        const projectsData = await projectsResponse.json();

        if (!isCancelled) {
          setCategories(categoriesData);
          setProjects(projectsData);
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
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={project.main_image} alt={project.title} />
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
        </div>
      </div>
    </section>
  );
}
