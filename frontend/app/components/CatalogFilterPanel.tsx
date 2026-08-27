"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";

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

const constructionTypeOptions = [
  { value: "timber", label: "Дом из бруса" },
  { value: "frame", label: "Каркасный дом" },
  { value: "log", label: "Дом из бревна" },
];

const floorsOptions = [
  { value: "1", label: "1 этаж", chipLabel: "1 этаж" },
  { value: "1.5", label: "1 + мансарда", chipLabel: "мансарда" },
  { value: "2", label: "2 этажа", chipLabel: "2 этажа" },
];

const materialOptions = [
  { value: "profiled", label: "Брус профилированный" },
  { value: "dry", label: "Брус камерной сушки" },
  { value: "regular", label: "Обычный брус" },
];

function formatRangeChip(min: string, max: string, unit: string) {
  if (min && max) return `${min}–${max} ${unit}`;
  if (min) return `от ${min} ${unit}`;
  return `до ${max} ${unit}`;
}

export function getActiveFilterChips(
  filters: Filters
): { key: FilterGroupKey; label: string }[] {
  const chips: { key: FilterGroupKey; label: string }[] = [];

  if (filters.construction_types.length) {
    chips.push({
      key: "construction_types",
      label: filters.construction_types
        .map(
          (value) =>
            constructionTypeOptions.find((option) => option.value === value)
              ?.label || value
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
        .map(
          (value) =>
            floorsOptions.find((option) => option.value === value)
              ?.chipLabel || value
        )
        .join(", "),
    });
  }

  if (filters.materials.length) {
    chips.push({
      key: "materials",
      label: filters.materials
        .map(
          (value) =>
            materialOptions.find((option) => option.value === value)?.label ||
            value
        )
        .join(", "),
    });
  }

  return chips;
}

type FilterSectionProps = {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: ReactNode;
};

function FilterSection({ title, isOpen, onToggle, children }: FilterSectionProps) {
  return (
    <div className={styles.section}>
      <button
        type="button"
        className={styles.sectionHeader}
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <span>{title}</span>
        <svg
          className={isOpen ? styles.chevronOpen : styles.chevron}
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path d="m5.5 7.5 4.5 5 4.5-5" />
        </svg>
      </button>

      {isOpen && <div className={styles.sectionBody}>{children}</div>}
    </div>
  );
}

type CheckboxListProps = {
  options: { value: string; label: string }[];
  selected: string[];
  onToggle: (value: string) => void;
};

function CheckboxList({ options, selected, onToggle }: CheckboxListProps) {
  return (
    <div className={styles.checkboxList}>
      {options.map((option) => (
        <label className={styles.checkboxRow} key={option.value}>
          <input
            type="checkbox"
            checked={selected.includes(option.value)}
            onChange={() => onToggle(option.value)}
          />
          <span>{option.label}</span>
        </label>
      ))}
    </div>
  );
}

type RangeInputsProps = {
  unit: string;
  minValue: string;
  maxValue: string;
  minPlaceholder?: string;
  maxPlaceholder?: string;
  onChangeMin: (value: string) => void;
  onChangeMax: (value: string) => void;
};

function RangeInputs({
  unit,
  minValue,
  maxValue,
  minPlaceholder,
  maxPlaceholder,
  onChangeMin,
  onChangeMax,
}: RangeInputsProps) {
  return (
    <div className={styles.rangeRow}>
      <label className={styles.rangeField}>
        <span>от</span>
        <span className={styles.rangeInputBox}>
          <input
            type="number"
            min="0"
            inputMode="decimal"
            value={minValue}
            placeholder={minPlaceholder}
            onChange={(event) => onChangeMin(event.target.value)}
          />
          <em>{unit}</em>
        </span>
      </label>
      <label className={styles.rangeField}>
        <span>до</span>
        <span className={styles.rangeInputBox}>
          <input
            type="number"
            min="0"
            inputMode="decimal"
            value={maxValue}
            placeholder={maxPlaceholder}
            onChange={(event) => onChangeMax(event.target.value)}
          />
          <em>{unit}</em>
        </span>
      </label>
    </div>
  );
}

type CatalogFilterPanelProps = {
  categories: ProjectCategory[];
  showCategoryFilter: boolean;
  filters: Filters;
  previewCount: number | null;
  isPreviewLoading: boolean;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
  onUpdateFilter: <K extends keyof Filters>(field: K, value: Filters[K]) => void;
  onToggleListFilter: (
    field: "construction_types" | "floors_list" | "materials",
    value: string
  ) => void;
  onSubmit: () => void;
  onReset: () => void;
};

export default function CatalogFilterPanel({
  categories,
  showCategoryFilter,
  filters,
  previewCount,
  isPreviewLoading,
  isMobileOpen,
  onCloseMobile,
  onUpdateFilter,
  onToggleListFilter,
  onSubmit,
  onReset,
}: CatalogFilterPanelProps) {
  const [openSections, setOpenSections] = useState({
    type: true,
    size: true,
    area: true,
    price: true,
    floors: true,
    material: true,
  });

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

  function toggleSection(key: keyof typeof openSections) {
    setOpenSections((current) => ({ ...current, [key]: !current[key] }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
    onCloseMobile();
  }

  const showButtonLabel = isPreviewLoading
    ? "Считаем…"
    : previewCount !== null
    ? `Показать ${previewCount} ${pluralizeProjects(previewCount)}`
    : "Показать проекты";

  const filterGroups = (
    <>
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

      <FilterSection
        title="Тип"
        isOpen={openSections.type}
        onToggle={() => toggleSection("type")}
      >
        <CheckboxList
          options={constructionTypeOptions}
          selected={filters.construction_types}
          onToggle={(value) => onToggleListFilter("construction_types", value)}
        />
      </FilterSection>

      <FilterSection
        title="Размер"
        isOpen={openSections.size}
        onToggle={() => toggleSection("size")}
      >
        <RangeInputs
          unit="м"
          minValue={filters.size_min}
          maxValue={filters.size_max}
          minPlaceholder="6"
          maxPlaceholder="10"
          onChangeMin={(value) => onUpdateFilter("size_min", value)}
          onChangeMax={(value) => onUpdateFilter("size_max", value)}
        />
      </FilterSection>

      <FilterSection
        title="Площадь"
        isOpen={openSections.area}
        onToggle={() => toggleSection("area")}
      >
        <RangeInputs
          unit="м²"
          minValue={filters.area_min}
          maxValue={filters.area_max}
          minPlaceholder="50"
          maxPlaceholder="120"
          onChangeMin={(value) => onUpdateFilter("area_min", value)}
          onChangeMax={(value) => onUpdateFilter("area_max", value)}
        />
      </FilterSection>

      <FilterSection
        title="Цена"
        isOpen={openSections.price}
        onToggle={() => toggleSection("price")}
      >
        <RangeInputs
          unit="₽"
          minValue={filters.price_min}
          maxValue={filters.price_max}
          onChangeMin={(value) => onUpdateFilter("price_min", value)}
          onChangeMax={(value) => onUpdateFilter("price_max", value)}
        />
      </FilterSection>

      <FilterSection
        title="Этажность"
        isOpen={openSections.floors}
        onToggle={() => toggleSection("floors")}
      >
        <CheckboxList
          options={floorsOptions}
          selected={filters.floors_list}
          onToggle={(value) => onToggleListFilter("floors_list", value)}
        />
      </FilterSection>

      <FilterSection
        title="Материал"
        isOpen={openSections.material}
        onToggle={() => toggleSection("material")}
      >
        <CheckboxList
          options={materialOptions}
          selected={filters.materials}
          onToggle={(value) => onToggleListFilter("materials", value)}
        />
      </FilterSection>
    </>
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
