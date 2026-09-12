"use client";

import { FormEvent, ReactNode, useEffect, useId } from "react";

import styles from "./CatalogFilterPanel.module.css";

export type ProjectCategory = {
  id: number;
  title: string;
  slug: string;
};

export type Filters = {
  category: string;
  construction_types: string[];
  floors_list: string[];
  materials: string[];
  size_min: string;
  size_max: string;
  area_min: string;
  area_max: string;
  price_min: string;
  price_max: string;
};

export type FilterGroupKey =
  | "construction_types"
  | "size"
  | "area"
  | "price"
  | "floors_list"
  | "materials";

export type RangeFilterKey = "size" | "area" | "price";

type ListFilterKey = "construction_types" | "floors_list" | "materials";

export const EMPTY_FILTERS: Omit<Filters, "category"> = {
  construction_types: [],
  floors_list: [],
  materials: [],
  size_min: "",
  size_max: "",
  area_min: "",
  area_max: "",
  price_min: "",
  price_max: "",
};

// Ответ /api/projects/facets/: варианты фильтров берутся из самих проектов
// (новый материал или этажность появятся в панели без правки кода), count —
// сколько проектов будет, если отметить вариант вдобавок к остальному.
export type FacetOption = {
  value: string;
  label: string;
  count: number;
};

export type FacetRange = {
  min: number;
  max: number;
  step: number;
};

export type CatalogFacets = {
  total: number;
  construction_types: FacetOption[];
  floors: FacetOption[];
  materials: FacetOption[];
  ranges: {
    size: FacetRange | null;
    area: FacetRange | null;
    price: FacetRange | null;
  };
};

function formatNumber(value: number | string) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString("ru-RU") : String(value);
}

// В каталоге бань «Дом из бруса» выглядел бы ошибкой.
function constructionTypeLabel(value: string, label: string, category: string) {
  if (value !== "timber") return label;
  return category === "baths" ? "Баня из бруса" : "Дом из бруса";
}

function optionLabel(options: FacetOption[] | undefined, value: string) {
  return options?.find((option) => option.value === value)?.label ?? value;
}

function formatRangeChip(min: string, max: string, unit: string) {
  if (min && max) return `${formatNumber(min)}–${formatNumber(max)} ${unit}`;
  if (min) return `от ${formatNumber(min)} ${unit}`;
  return `до ${formatNumber(max)} ${unit}`;
}

export function getActiveFilterChips(
  filters: Filters,
  facets: CatalogFacets | null
): { key: FilterGroupKey; label: string }[] {
  const chips: { key: FilterGroupKey; label: string }[] = [];

  if (filters.construction_types.length) {
    chips.push({
      key: "construction_types",
      label: filters.construction_types
        .map((value) =>
          constructionTypeLabel(
            value,
            optionLabel(facets?.construction_types, value),
            filters.category
          )
        )
        .join(", "),
    });
  }

  if (filters.size_min || filters.size_max) {
    chips.push({
      key: "size",
      label: formatRangeChip(filters.size_min, filters.size_max, "м"),
    });
  }

  if (filters.area_min || filters.area_max) {
    chips.push({
      key: "area",
      label: formatRangeChip(filters.area_min, filters.area_max, "м²"),
    });
  }

  if (filters.price_min || filters.price_max) {
    chips.push({
      key: "price",
      label: formatRangeChip(filters.price_min, filters.price_max, "₽"),
    });
  }

  if (filters.floors_list.length) {
    chips.push({
      key: "floors_list",
      label: filters.floors_list
        .map((value) => optionLabel(facets?.floors, value))
        .join(", "),
    });
  }

  if (filters.materials.length) {
    chips.push({
      key: "materials",
      label: filters.materials
        .map((value) => optionLabel(facets?.materials, value))
        .join(", "),
    });
  }

  return chips;
}

type SectionProps = {
  title: string;
  unit?: string;
  children: ReactNode;
};

function FilterSection({ title, unit, children }: SectionProps) {
  const titleId = useId();

  return (
    <div className={styles.section} role="group" aria-labelledby={titleId}>
      <p className={styles.sectionTitle} id={titleId}>
        {title}
        {unit && <small>{unit}</small>}
      </p>
      {children}
    </div>
  );
}

type OptionsProps = {
  options: FacetOption[];
  selected: string[];
  onToggle: (value: string) => void;
};

// Вариант, с которым ничего не найдётся, виден, но недоступен — пока его не
// отметили (иначе отмеченный по старой ссылке вариант было бы не снять).
function isUnavailable(option: FacetOption, selected: string[]) {
  return option.count === 0 && !selected.includes(option.value);
}

function PillOptions({ options, selected, onToggle }: OptionsProps) {
  return (
    <div className={styles.pills}>
      {options.map((option) => {
        const checked = selected.includes(option.value);
        const unavailable = isUnavailable(option, selected);

        return (
          <label
            key={option.value}
            className={[
              styles.pill,
              checked ? styles.pillChecked : "",
              unavailable ? styles.optionUnavailable : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <input
              className={styles.hiddenCheckbox}
              type="checkbox"
              checked={checked}
              disabled={unavailable}
              onChange={() => onToggle(option.value)}
            />
            <span>{option.label}</span>
            <em className={styles.count}>{option.count}</em>
          </label>
        );
      })}
    </div>
  );
}

function CheckboxOptions({ options, selected, onToggle }: OptionsProps) {
  return (
    <div className={styles.checkboxList}>
      {options.map((option) => {
        const unavailable = isUnavailable(option, selected);

        return (
          <label
            key={option.value}
            className={`${styles.checkboxRow} ${
              unavailable ? styles.optionUnavailable : ""
            }`}
          >
            <input
              type="checkbox"
              checked={selected.includes(option.value)}
              disabled={unavailable}
              onChange={() => onToggle(option.value)}
            />
            <span className={styles.optionLabel}>{option.label}</span>
            <em className={styles.count}>{option.count}</em>
          </label>
        );
      })}
    </div>
  );
}

function parseValue(value: string) {
  if (!value) return null;
  const number = Number(value.replace(",", "."));
  return Number.isFinite(number) ? number : null;
}

function sanitizeTypedValue(value: string, wholeNumbers: boolean) {
  if (wholeNumbers) return value.replace(/\D/g, "");

  const [whole, ...fraction] = value
    .replace(",", ".")
    .replace(/[^\d.]/g, "")
    .split(".");
  return fraction.length ? `${whole}.${fraction.join("")}` : whole;
}

type RangeFilterProps = {
  title: string;
  unit: string;
  range: FacetRange | null;
  minValue: string;
  maxValue: string;
  wholeNumbers?: boolean;
  onChange: (min: string, max: string) => void;
};

// Ползунок с двумя бегунками и поля «от / до» для точного значения. Шкала
// приходит с бэкенда (catalog/filters.py): до самого большого проекта
// выборки, размер и площадь — от 1. Бегунок у края шкалы — это «без
// ограничения»: пустое значение, фильтр не применяется.
function RangeFilter({
  title,
  unit,
  range,
  minValue,
  maxValue,
  wholeNumbers = false,
  onChange,
}: RangeFilterProps) {
  const hasScale = Boolean(range && range.max > range.min);
  if (!hasScale && !minValue && !maxValue) return null;

  const scaleMin = range?.min ?? 0;
  const scaleMax = range?.max ?? 0;
  const span = scaleMax - scaleMin || 1;
  const clampToScale = (value: number) =>
    Math.min(Math.max(value, scaleMin), scaleMax);
  const low = clampToScale(parseValue(minValue) ?? scaleMin);
  const high = clampToScale(parseValue(maxValue) ?? scaleMax);
  const from = Math.min(low, high);
  const to = Math.max(low, high);
  const fromPercent = ((from - scaleMin) / span) * 100;
  const toPercent = ((to - scaleMin) / span) * 100;

  const display = (value: string) =>
    wholeNumbers && value ? formatNumber(value) : value.replace(".", ",");

  return (
    <FilterSection title={title} unit={unit}>
      {hasScale && (
        <div className={styles.slider}>
          <span className={styles.sliderTrack}>
            <span
              className={styles.sliderFill}
              style={{ left: `${fromPercent}%`, right: `${100 - toPercent}%` }}
            />
          </span>
          <input
            className={styles.sliderInput}
            type="range"
            min={scaleMin}
            max={scaleMax}
            step={range?.step}
            value={from}
            // Бегунки сошлись у правого края — сверху должен быть левый, иначе
            // его не сдвинуть.
            style={{ zIndex: fromPercent > 50 ? 3 : 2 }}
            aria-label={`${title}: от`}
            aria-valuetext={`от ${formatNumber(from)} ${unit}`}
            onChange={(event) => {
              const value = Math.min(Number(event.target.value), to);
              onChange(value <= scaleMin ? "" : String(value), maxValue);
            }}
          />
          <input
            className={styles.sliderInput}
            type="range"
            min={scaleMin}
            max={scaleMax}
            step={range?.step}
            value={to}
            style={{ zIndex: 2 }}
            aria-label={`${title}: до`}
            aria-valuetext={`до ${formatNumber(to)} ${unit}`}
            onChange={(event) => {
              const value = Math.max(Number(event.target.value), from);
              onChange(minValue, value >= scaleMax ? "" : String(value));
            }}
          />
        </div>
      )}

      <div className={styles.rangeInputs}>
        <input
          className={styles.rangeInput}
          type="text"
          inputMode={wholeNumbers ? "numeric" : "decimal"}
          value={display(minValue)}
          placeholder={hasScale ? `от ${formatNumber(scaleMin)}` : "от"}
          aria-label={`${title}, ${unit}: от`}
          onChange={(event) =>
            onChange(sanitizeTypedValue(event.target.value, wholeNumbers), maxValue)
          }
        />
        <input
          className={styles.rangeInput}
          type="text"
          inputMode={wholeNumbers ? "numeric" : "decimal"}
          value={display(maxValue)}
          placeholder={hasScale ? `до ${formatNumber(scaleMax)}` : "до"}
          aria-label={`${title}, ${unit}: до`}
          onChange={(event) =>
            onChange(minValue, sanitizeTypedValue(event.target.value, wholeNumbers))
          }
        />
      </div>
    </FilterSection>
  );
}

type CatalogFilterPanelProps = {
  categories: ProjectCategory[];
  showCategoryFilter: boolean;
  filters: Filters;
  facets: CatalogFacets | null;
  isFacetsLoading: boolean;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
  onUpdateFilter: <K extends keyof Filters>(field: K, value: Filters[K]) => void;
  onUpdateRange: (field: RangeFilterKey, min: string, max: string) => void;
  onToggleListFilter: (field: ListFilterKey, value: string) => void;
  onSubmit: () => void;
  onReset: () => void;
};

export default function CatalogFilterPanel({
  categories,
  showCategoryFilter,
  filters,
  facets,
  isFacetsLoading,
  isMobileOpen,
  onCloseMobile,
  onUpdateFilter,
  onUpdateRange,
  onToggleListFilter,
  onSubmit,
  onReset,
}: CatalogFilterPanelProps) {
  useEffect(() => {
    if (!isMobileOpen) return;

    const body = document.body;
    const previousOverflow = body.style.overflow;
    body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onCloseMobile();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMobileOpen, onCloseMobile]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
    onCloseMobile();
  }

  const showButtonLabel = facets
    ? `Показать ${facets.total} ${pluralizeProjects(facets.total)}`
    : "Показать проекты";

  // «Тип» с единственным вариантом ничего не отбирает — не занимаем им место.
  const typeOptions = (facets?.construction_types ?? []).map((option) => ({
    ...option,
    label: constructionTypeLabel(option.value, option.label, filters.category),
  }));
  const showTypeFilter =
    typeOptions.length > 1 || filters.construction_types.length > 0;

  const filterGroups = (
    <div
      className={`${styles.groups} ${isFacetsLoading ? styles.counting : ""}`}
    >
      {showCategoryFilter && (
        <label className={styles.plainSelect}>
          <span>Категория</span>
          <select
            value={filters.category}
            onChange={(event) => onUpdateFilter("category", event.target.value)}
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

      {facets === null ? (
        <div className={styles.skeleton} aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      ) : (
        <>
          {showTypeFilter && (
            <FilterSection title="Тип">
              <CheckboxOptions
                options={typeOptions}
                selected={filters.construction_types}
                onToggle={(value) =>
                  onToggleListFilter("construction_types", value)
                }
              />
            </FilterSection>
          )}

          <RangeFilter
            title="Размер"
            unit="м"
            range={facets.ranges.size}
            minValue={filters.size_min}
            maxValue={filters.size_max}
            onChange={(min, max) => onUpdateRange("size", min, max)}
          />

          <RangeFilter
            title="Площадь"
            unit="м²"
            range={facets.ranges.area}
            minValue={filters.area_min}
            maxValue={filters.area_max}
            wholeNumbers
            onChange={(min, max) => onUpdateRange("area", min, max)}
          />

          <RangeFilter
            title="Цена"
            unit="₽"
            range={facets.ranges.price}
            minValue={filters.price_min}
            maxValue={filters.price_max}
            wholeNumbers
            onChange={(min, max) => onUpdateRange("price", min, max)}
          />

          {facets.floors.length > 0 && (
            <FilterSection title="Этажность">
              <PillOptions
                options={facets.floors}
                selected={filters.floors_list}
                onToggle={(value) => onToggleListFilter("floors_list", value)}
              />
            </FilterSection>
          )}

          {facets.materials.length > 0 && (
            <FilterSection title="Материал">
              <CheckboxOptions
                options={facets.materials}
                selected={filters.materials}
                onToggle={(value) => onToggleListFilter("materials", value)}
              />
            </FilterSection>
          )}
        </>
      )}
    </div>
  );

  return (
    <>
      {/* Десктоп: постоянная боковая панель. Скрывается через CSS на узких
          экранах — см. CatalogFilterPanel.module.css. */}
      <aside className={`catalogSidebar ${styles.desktopPanel}`}>
        <div className={styles.panelHeading}>
          <strong>Подбор проекта</strong>
          <button type="button" className={styles.resetLink} onClick={onReset}>
            Сбросить
          </button>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          {filterGroups}
          <button className={`buttonPrimary ${styles.submitButton}`} type="submit">
            {showButtonLabel}
          </button>
        </form>
      </aside>

      {isMobileOpen && (
        <div
          className={styles.mobileOverlay}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) onCloseMobile();
          }}
        >
          <div className={styles.mobileSheet} role="dialog" aria-modal="true" aria-label="Фильтры каталога">
            <div className={styles.mobileHeader}>
              <strong>Фильтры</strong>
              <button
                type="button"
                className={styles.resetLink}
                onClick={onReset}
              >
                Сбросить
              </button>
              <button
                type="button"
                className={styles.mobileClose}
                aria-label="Закрыть фильтры"
                onClick={onCloseMobile}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 6 18 18M18 6 6 18" />
                </svg>
              </button>
            </div>

            <form className={styles.mobileForm} onSubmit={handleSubmit}>
              <div className={styles.mobileScroll}>{filterGroups}</div>
              <div className={styles.mobileFooter}>
                <button className={`buttonPrimary ${styles.submitButton}`} type="submit">
                  {showButtonLabel}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

function pluralizeProjects(count: number) {
  const mod10 = count % 10;
  const mod100 = count % 100;

  if (mod10 === 1 && mod100 !== 11) return "проект";
  if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) return "проекта";
  return "проектов";
}
