"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { reachGoal } from "../lib/metrika";
import { SITE_PHONE, SITE_PHONE_HREF } from "../lib/site";

type MaterialOption = {
  code: string;
  title: string;
  description?: string;
};

type ExtraOption = {
  code: string;
  title: string;
};

type FloorOption = {
  value: string;
  label: string;
};

type CalculatorConfig = {
  area: {
    min: number;
    max: number;
  };
  floors: FloorOption[];
  materials: MaterialOption[];
  foundations: ExtraOption[];
  roofs: ExtraOption[];
  pricing_basis: string;
  package_label: string;
  disclaimer: string;
  engine?: string;
  rate_history?: boolean;
  requires_dimensions?: boolean;
};


type SimilarProject = {
  slug: string;
  title: string;
  area: number;
  size_text: string;
  floor_label: string;
  price_from: number | null;
  main_image: string | null;
};

type CalculationResult = {
  total: number;
  price_min: number;
  price_max: number;
  range_percent: number;
  breakdown: Array<{
    code: string;
    title: string;
    price: number;
    note: string;
  }>;
  similar_projects?: SimilarProject[];
  method: string;
  confidence: "high" | "medium" | "preliminary";
  calculation_mode?: "quick" | "explicit" | "verified_project";
  price_date?: string;
  confidence_label: string;
  assumptions?: string[];
  component_details?: {
    house?: {
      base_before_indexation?: number;
      pricing_multiplier?: number;
      lines?: Array<{
        code: string;
        title: string;
        quantity: number;
        unit: string;
        rate: number;
        base_amount: number;
        rate_meta?: { source?: string; valid_from?: string; fallback_component?: string | null };
      }>;
    };
  };
  disclaimer: string;
};

type FormState = {
  area: string;
  width: string;
  length: string;
  floors: string;
  bedrooms: string;
  material: string;
  foundation: string;
  roof: string;
  internalWallLength: string;
  openingsArea: string;
  roofArea: string;
  pileCount: string;
  projectRef: string;
  externalWallVolume: string;
  internalWallVolume: string;
  beamsVolume: string;
  raftersVolume: string;
  lathingVolume: string;
  otherLumberVolume: string;
  gableArea: string;
  terraceArea: string;
};

const presets = [
  { label: "ДБ-01", area: "52", width: "6", length: "6", floors: "1.5", bedrooms: "2" },
  { label: "ДБ-02", area: "68", width: "6", length: "6", floors: "1.5", bedrooms: "2" },
  { label: "ДБ-03", area: "105", width: "7", length: "9", floors: "2", bedrooms: "4" },
];

const priceFormatter = new Intl.NumberFormat("ru-RU");

function formatPrice(value: number) {
  return `${priceFormatter.format(value)} ₽`;
}

function getApiError(data: unknown) {
  if (!data || typeof data !== "object") {
    return "Не удалось выполнить расчёт";
  }

  const payload = data as Record<string, unknown>;

  if (typeof payload.detail === "string") {
    return payload.detail;
  }

  const nonField = payload.non_field_errors;
  if (Array.isArray(nonField) && typeof nonField[0] === "string") {
    return nonField[0];
  }

  for (const value of Object.values(payload)) {
    if (Array.isArray(value) && typeof value[0] === "string") {
      return value[0];
    }
  }

  return "Проверьте введённые параметры";
}

export default function HouseCalculator() {
  const [config, setConfig] = useState<CalculatorConfig | null>(null);
  const [form, setForm] = useState<FormState>({
    area: "52",
    width: "6",
    length: "6",
    floors: "1.5",
    bedrooms: "2",
    material: "",
    foundation: "",
    roof: "",
    internalWallLength: "",
    openingsArea: "",
    roofArea: "",
    pileCount: "",
    projectRef: "",
    externalWallVolume: "",
    internalWallVolume: "",
    beamsVolume: "",
    raftersVolume: "",
    lathingVolume: "",
    otherLumberVolume: "",
    gableArea: "",
    terraceArea: "",
  });
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadConfig() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        const response = await fetch(`${apiUrl}/calculator/config/`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("Калькулятор пока недоступен");
        }

        const data: CalculatorConfig = await response.json();

        if (!cancelled) {
          setConfig(data);
          setForm((current) => ({
            ...current,
            material: current.material || data.materials[0]?.code || "",
          }));
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Не удалось загрузить настройки калькулятора"
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingConfig(false);
        }
      }
    }

    loadConfig();

    return () => {
      cancelled = true;
    };
  }, []);

  const footprint = useMemo(() => {
    const width = Number(form.width.replace(",", "."));
    const length = Number(form.length.replace(",", "."));

    if (!Number.isFinite(width) || !Number.isFinite(length) || width <= 0 || length <= 0) {
      return null;
    }

    return width * length;
  }, [form.width, form.length]);

  const geometryWarning = useMemo(() => {
    if (!footprint) return "";
    const area = Number(form.area.replace(",", "."));
    const floors = Number(form.floors);
    if (!Number.isFinite(area) || !Number.isFinite(floors)) return "";
    const maxFactor = floors === 1 ? 1.05 : 2.05;
    const maxArea = footprint * maxFactor;
    if (area > maxArea) {
      return `Площадь ${area.toLocaleString("ru-RU")} м² не соответствует габаритам ${form.width}×${form.length} м и этажности ${form.floors}. Максимум по геометрической проверке — около ${Math.floor(maxArea)} м².`;
    }
    return "";
  }, [footprint, form.area, form.floors, form.width, form.length]);

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setResult(null);
    setError("");
  }

  function applyPreset(preset: (typeof presets)[number]) {
    setForm((current) => ({
      ...current,
      area: preset.area,
      width: preset.width,
      length: preset.length,
      floors: preset.floors,
      bedrooms: preset.bedrooms,
      foundation: "",
      roof: "",
      internalWallLength: "",
      openingsArea: "",
      roofArea: "",
      pileCount: "",
      projectRef: "",
      externalWallVolume: "",
      internalWallVolume: "",
      beamsVolume: "",
      raftersVolume: "",
      lathingVolume: "",
      otherLumberVolume: "",
      gableArea: "",
      terraceArea: "",
    }));
    setResult(null);
    setError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (geometryWarning) {
      setError(geometryWarning);
      return;
    }
    setIsCalculating(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const body: Record<string, string> = {
        area: form.area.replace(",", "."),
        floors: form.floors,
        material: form.material,
        foundation: form.foundation,
        roof: form.roof,
        width: form.width.replace(",", "."),
        length: form.length.replace(",", "."),
      };

      if (form.bedrooms.trim()) {
        body.bedrooms = form.bedrooms;
      }
      if (form.internalWallLength.trim()) {
        body.internal_wall_length_m = form.internalWallLength.replace(",", ".");
      }
      if (form.openingsArea.trim()) {
        body.external_openings_area_m2 = form.openingsArea.replace(",", ".");
      }
      if (form.roofArea.trim()) {
        body.roof_area = form.roofArea.replace(",", ".");
      }
      if (form.pileCount.trim() && form.foundation) {
        body.foundation_pile_count = form.pileCount;
      }
      if (form.projectRef.trim()) body.project = form.projectRef.trim();
      if (form.externalWallVolume.trim()) body.external_wall_volume_m3 = form.externalWallVolume.replace(",", ".");
      if (form.internalWallVolume.trim()) body.internal_wall_volume_m3 = form.internalWallVolume.replace(",", ".");
      if (form.beamsVolume.trim()) body.beams_volume_m3 = form.beamsVolume.replace(",", ".");
      if (form.raftersVolume.trim()) body.rafters_volume_m3 = form.raftersVolume.replace(",", ".");
      if (form.lathingVolume.trim()) body.lathing_volume_m3 = form.lathingVolume.replace(",", ".");
      if (form.otherLumberVolume.trim()) body.other_structural_lumber_volume_m3 = form.otherLumberVolume.replace(",", ".");
      if (form.gableArea.trim()) body.gable_area = form.gableArea.replace(",", ".");
      if (form.terraceArea.trim()) body.terrace_area = form.terraceArea.replace(",", ".");

      const response = await fetch(`${apiUrl}/calculator/calculate/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(getApiError(data));
      }

      setResult(data as CalculationResult);
      reachGoal("calculator_completed");
    } catch (calculationError) {
      setResult(null);
      setError(
        calculationError instanceof Error
          ? calculationError.message
          : "Не удалось выполнить расчёт"
      );
    } finally {
      setIsCalculating(false);
    }
  }

  if (isLoadingConfig) {
    return <div className="calculatorState">Загружаем параметры калькулятора…</div>;
  }

  if (!config) {
    return (
      <div className="calculatorState calculatorStateError">
        {error || "Калькулятор пока недоступен"}
      </div>
    );
  }

  return (
    <div className="calculatorWorkspace">
      <section className="calculatorPanel">
        <div className="calculatorPanelHeader">
          <div>
            <span className="calculatorStep">01</span>
            <h2>Параметры дома</h2>
          </div>
          <p>{config.package_label}</p>
        </div>

        <div className="calculatorPresets" aria-label="Быстрые примеры">
          <span>Быстрая проверка:</span>
          {presets.map((preset) => (
            <button type="button" key={preset.label} onClick={() => applyPreset(preset)}>
              {preset.label} · {preset.width}×{preset.length} · {preset.area} м²
            </button>
          ))}
        </div>

        <form className="calculatorForm" onSubmit={handleSubmit}>
          <div className="calculatorFieldGrid">
            <label className="calculatorField calculatorFieldEmphasis">
              <span>Общая площадь, м²</span>
              <input
                type="number"
                inputMode="decimal"
                min={config.area.min}
                max={config.area.max}
                step="0.1"
                value={form.area}
                onChange={(event) => updateField("area", event.target.value)}
                required
              />
              <small>От {config.area.min} до {config.area.max} м²</small>
            </label>

            <label className="calculatorField">
              <span>Этажность</span>
              <select
                value={form.floors}
                onChange={(event) => updateField("floors", event.target.value)}
              >
                {config.floors.map((floor) => (
                  <option key={floor.value} value={floor.value}>
                    {floor.label}
                  </option>
                ))}
              </select>
              <small>Определяет объём стен и конструкций верхнего этажа</small>
            </label>
          </div>

          <fieldset className="calculatorFieldset">
            <legend>Габариты дома</legend>
            <p>
              Обязательны: по габаритам считаются периметр стен, пятно застройки,
              перекрытия, стропильная система, фундамент и кровля.
            </p>

            <div className="calculatorFieldGrid calculatorDimensions">
              <label className="calculatorField">
                <span>Ширина, м</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min="2"
                  step="0.1"
                  value={form.width}
                  onChange={(event) => updateField("width", event.target.value)}
                  placeholder="6"
                  required
                />
              </label>

              <span className="calculatorDimensionSign">×</span>

              <label className="calculatorField">
                <span>Длина, м</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min="2"
                  step="0.1"
                  value={form.length}
                  onChange={(event) => updateField("length", event.target.value)}
                  placeholder="8"
                  required
                />
              </label>

              {footprint && (
                <div className="calculatorFootprint">
                  <span>Пятно застройки</span>
                  <strong>{footprint.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} м²</strong>
                </div>
              )}
            </div>

            {geometryWarning && <div className="calculatorError">{geometryWarning}</div>}

            <div className="calculatorFieldGrid">
              <label className="calculatorField">
                <span>Спальни / основные комнаты</span>
                <input
                  type="number"
                  inputMode="numeric"
                  min="1"
                  max="20"
                  step="1"
                  value={form.bedrooms}
                  onChange={(event) => updateField("bedrooms", event.target.value)}
                />
                <small>Помогает оценить длину внутренних перегородок. В точной смете берём её из плана.</small>
              </label>
            </div>
          </fieldset>

          <details className="calculatorFieldset">
            <summary><strong>Расширенные параметры для точной проверки</strong></summary>
            <p>
              Необязательно для посетителя. Если значения известны из планировки или сметы,
              они заменяют автоматические допущения калькулятора.
            </p>
            <div className="calculatorFieldGrid">
              <label className="calculatorField">
                <span>Длина внутренних перегородок, м</span>
                <input
                  type="number" inputMode="decimal" min="0" step="0.1"
                  value={form.internalWallLength}
                  onChange={(event) => updateField("internalWallLength", event.target.value)}
                  placeholder="например, 24.5"
                />
              </label>
              <label className="calculatorField">
                <span>Площадь окон и дверей наружных стен, м²</span>
                <input
                  type="number" inputMode="decimal" min="0" step="0.1"
                  value={form.openingsArea}
                  onChange={(event) => updateField("openingsArea", event.target.value)}
                  placeholder="например, 14.2"
                />
              </label>
              <label className="calculatorField">
                <span>Фактическая площадь крыши, м²</span>
                <input
                  type="number" inputMode="decimal" min="1" step="0.1"
                  value={form.roofArea}
                  onChange={(event) => updateField("roofArea", event.target.value)}
                  placeholder="если известна из проекта"
                />
              </label>
              <label className="calculatorField">
                <span>Количество свай</span>
                <input
                  type="number" inputMode="numeric" min="1" step="1"
                  value={form.pileCount}
                  onChange={(event) => updateField("pileCount", event.target.value)}
                  placeholder="если рассчитано инженером"
                />
              </label>
              <label className="calculatorField">
                <span>Код проекта / техпаспорта</span>
                <input value={form.projectRef} onChange={(event) => updateField("projectRef", event.target.value)} placeholder="например, DB-01" />
                <small>Для внутренней проверки: подтянет заполненные технические количества проекта.</small>
              </label>
              <label className="calculatorField">
                <span>Наружные стены, м³</span>
                <input type="number" min="0" step="0.001" value={form.externalWallVolume} onChange={(event) => updateField("externalWallVolume", event.target.value)} />
              </label>
              <label className="calculatorField">
                <span>Перегородки, м³</span>
                <input type="number" min="0" step="0.001" value={form.internalWallVolume} onChange={(event) => updateField("internalWallVolume", event.target.value)} />
              </label>
              <label className="calculatorField">
                <span>Балки/лаги, м³</span>
                <input type="number" min="0" step="0.001" value={form.beamsVolume} onChange={(event) => updateField("beamsVolume", event.target.value)} />
              </label>
              <label className="calculatorField">
                <span>Стропила/ригели, м³</span>
                <input type="number" min="0" step="0.001" value={form.raftersVolume} onChange={(event) => updateField("raftersVolume", event.target.value)} />
              </label>
              <label className="calculatorField">
                <span>Обрешётка, м³</span>
                <input type="number" min="0" step="0.001" value={form.lathingVolume} onChange={(event) => updateField("lathingVolume", event.target.value)} />
              </label>
              <label className="calculatorField">
                <span>Прочий пиломатериал, м³</span>
                <input type="number" min="0" step="0.001" value={form.otherLumberVolume} onChange={(event) => updateField("otherLumberVolume", event.target.value)} />
              </label>
              <label className="calculatorField">
                <span>Фронтоны, м²</span>
                <input type="number" min="0" step="0.1" value={form.gableArea} onChange={(event) => updateField("gableArea", event.target.value)} />
              </label>
              <label className="calculatorField">
                <span>Терраса в комплектации, м²</span>
                <input type="number" min="0" step="0.1" value={form.terraceArea} onChange={(event) => updateField("terraceArea", event.target.value)} />
              </label>
            </div>
          </details>

          <fieldset className="calculatorFieldset">
            <legend>Материал стен</legend>
            <div className="calculatorMaterialGrid">
              {config.materials.map((material) => (
                <label
                  className={`calculatorChoice ${
                    form.material === material.code ? "calculatorChoiceActive" : ""
                  }`}
                  key={material.code}
                >
                  <input
                    type="radio"
                    name="material"
                    value={material.code}
                    checked={form.material === material.code}
                    onChange={(event) => updateField("material", event.target.value)}
                  />
                  <strong>{material.title}</strong>
                  {material.description && <span>{material.description}</span>}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="calculatorFieldset">
            <legend>Дополнительно</legend>
            <p>
              Эти позиции считаются отдельно от базовой комплектации. Для них нужны
              габариты дома.
            </p>

            <div className="calculatorFieldGrid">
              <label className="calculatorField">
                <span>Фундамент</span>
                <select
                  value={form.foundation}
                  onChange={(event) => updateField("foundation", event.target.value)}
                >
                  <option value="">Не учитывать</option>
                  {config.foundations.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.title}
                    </option>
                  ))}
                </select>
              </label>

              <label className="calculatorField">
                <span>Чистовая кровля</span>
                <select value={form.roof} onChange={(event) => updateField("roof", event.target.value)}>
                  <option value="">Не учитывать</option>
                  {config.roofs.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.title}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </fieldset>

          {error && <div className="calculatorError">{error}</div>}

          <button className="buttonPrimary calculatorSubmit" type="submit" disabled={isCalculating || Boolean(geometryWarning)}>
            {isCalculating ? "Считаем…" : "Рассчитать стоимость"}
          </button>

          <p className="calculatorBasis">{config.pricing_basis}</p>
        </form>
      </section>

      <aside className="calculatorResultPanel" aria-live="polite">
        {!result ? (
          <div className="calculatorResultEmpty">
            <span className="calculatorStep">02</span>
            <h2>Предварительная стоимость</h2>
            <p>
              Заполните параметры слева. Калькулятор сформирует ведомость объёмов и умножит каждую позицию на действующую сметную ставку.
            </p>

            <div className="calculatorResultHint">
              <strong>Это не поиск похожего дома</strong>
              <p>
                Сначала определяются количества, затем каждая позиция умножается на историческую ставку, действующую на дату расчёта. Ниже дополнительно покажем реальные проекты каталога похожего размера — для сравнения.
              </p>
            </div>
          </div>
        ) : (
          <div className="calculatorResult">
            <span className="calculatorStep">02</span>
            <p className="calculatorResultLabel">Ориентировочный диапазон</p>
            <h2>
              {formatPrice(result.price_min)} — {formatPrice(result.price_max)}
            </h2>
            <p className="calculatorResultExact">
              Расчётная точка: <strong>{formatPrice(result.total)}</strong>
            </p>

            <div className={`calculatorConfidence calculatorConfidence-${result.confidence}`}>
              <span>Точность ориентира</span>
              <strong>{result.confidence_label}</strong>
            </div>

            <div className="calculatorBreakdown">
              <h3>Из чего сложилась сумма</h3>
              {result.breakdown.map((item) => (
                <div className="calculatorBreakdownRow" key={item.code}>
                  <div>
                    <strong>{item.title}</strong>
                    <span>{item.note}</span>
                  </div>
                  <b>{formatPrice(item.price)}</b>
                </div>
              ))}
            </div>

            {result.component_details?.house?.lines?.length ? (
              <div className="calculatorReferences">
                <h3>Смета комплектации дома</h3>
                <p>Расчётные количества до индексации и округления.</p>
                {result.component_details.house.lines.map((line) => (
                  <div className="calculatorBreakdownRow" key={line.code}>
                    <div>
                      <strong>{line.title}</strong>
                      <span>
                        {line.quantity.toLocaleString("ru-RU", { maximumFractionDigits: 2 })} {line.unit}
                        {` × ${formatPrice(line.rate)}`}{line.rate_meta?.valid_from ? ` · ставка с ${line.rate_meta.valid_from}` : ""}
                      </span>
                    </div>
                    <b>{formatPrice(line.base_amount)}</b>
                  </div>
                ))}
              </div>
            ) : null}

            {result.assumptions?.length ? (
              <div className="calculatorReferences">
                <h3>Что калькулятор оценил автоматически</h3>
                {result.assumptions.map((item) => <p key={item}>{item}</p>)}
              </div>
            ) : null}

            <div className="calculatorResultActions">
              <a className="buttonPrimary" href="#calculator-lead">
                Получить точную смету
              </a>
              <button className="buttonGhost" type="button" onClick={() => setResult(null)}>
                Изменить параметры
              </button>
            </div>

            <p className="calculatorDisclaimer">{result.disclaimer}</p>

            {result.similar_projects && result.similar_projects.length > 0 && (
              <div className="calculatorSimilar">
                <h3>Похожие проекты в каталоге</h3>
                <p>
                  Реальные проекты близкого размера и их фактическая цена — ориентир в дополнение к расчёту выше.
                </p>
                {result.similar_projects.map((project) => (
                  <Link className="calculatorSimilarRow" href={`/projects/${project.slug}`} key={project.slug}>
                    <span className="calculatorSimilarThumb">
                      {project.main_image ? (
                        <Image
                          src={project.main_image}
                          alt={project.title}
                          fill
                          sizes="52px"
                          style={{ objectFit: "cover" }}
                        />
                      ) : null}
                    </span>
                    <span className="calculatorSimilarInfo">
                      <strong>{project.title}</strong>
                      <span>
                        {project.size_text || `${project.area} м²`}
                        {project.floor_label ? ` · ${project.floor_label}` : ""}
                      </span>
                    </span>
                    <b>{project.price_from ? formatPrice(project.price_from) : "Цена по запросу"}</b>
                  </Link>
                ))}
                <p className="calculatorSimilarNote">
                  Цены проектов каталога могли измениться — точную стоимость на сегодня уточните по
                  телефону{" "}
                  <a
                    href={`tel:${SITE_PHONE_HREF}`}
                    onClick={() => reachGoal("phone_click", { location: "calculator_result" })}
                  >
                    {SITE_PHONE}
                  </a>
                  .
                </p>
              </div>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
