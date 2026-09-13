"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState, type TouchEvent } from "react";

import LeadFormButton from "./LeadFormButton";
import LightboxViewer from "./LightboxViewer";
import styles from "./ProjectGalleryWithPrices.module.css";

export type ProjectMediaItem = {
  id: string | number;
  src: string;
  alt: string;
  caption?: string;
  kind?: string;
};

export type ProjectPriceItem = {
  id: string | number;
  title: string;
  price: string;
};

export type ProjectPriceGroup = {
  title: string;
  items: ProjectPriceItem[];
};

// Примерная цена «всё вместе»: самый доступный комплект материалов, фундамент
// и кровля проекта. Строки уже отформатированы на сервере (projects/[slug]).
export type ProjectStartingPrice = {
  total: string;
  materials: string;
  foundation: string;
  roof: string;
};

type ProjectGalleryWithPricesProps = {
  images: ProjectMediaItem[];
  priceGroups: ProjectPriceGroup[];
  // Заявка из «Получить точный расчёт» привязывается к этому проекту.
  projectSlug?: string;
  startingPrice?: ProjectStartingPrice | null;
};

function ArrowLeftIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m14.5 5-7 7 7 7" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m9.5 5 7 7-7 7" />
    </svg>
  );
}

function ExpandIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
    </svg>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      className={open ? styles.chevronOpen : undefined}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path d="m7 10 5 5 5-5" />
    </svg>
  );
}

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7.2 3.7 9.8 7a1.5 1.5 0 0 1-.2 2l-1.3 1.1a14.2 14.2 0 0 0 5.6 5.6l1.1-1.3a1.5 1.5 0 0 1 2-.2l3.3 2.6a1.5 1.5 0 0 1 .4 1.8l-.7 1.6a2.7 2.7 0 0 1-2.7 1.6C9.1 21 3 14.9 2.2 6.7A2.7 2.7 0 0 1 3.8 4l1.6-.7a1.5 1.5 0 0 1 1.8.4Z" />
    </svg>
  );
}

// Строка цены под заголовком материала: «Обычный брус 150х150» под «Обычный
// брус» → «150×150 мм». Название материала уже есть в заголовке группы.
function priceItemLabel(itemTitle: string, groupTitle: string) {
  const rest = itemTitle.startsWith(groupTitle)
    ? itemTitle.slice(groupTitle.length).trim()
    : itemTitle;
  const section = rest.match(/^(\d+)\s*[xXхХ×]\s*(\d+)$/);
  if (section) return `${section[1]}×${section[2]} мм`;
  return rest || itemTitle;
}

export default function ProjectGalleryWithPrices({
  images,
  priceGroups,
  projectSlug,
  startingPrice,
}: ProjectGalleryWithPricesProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [openPriceGroups, setOpenPriceGroups] = useState<Record<string, boolean>>(
    () => Object.fromEntries(priceGroups.map((group) => [group.title, true])),
  );

  const thumbnailRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const touchStartX = useRef<number | null>(null);

  const safeIndex = images.length
    ? Math.min(Math.max(selectedIndex, 0), images.length - 1)
    : 0;
  const activeImage = images[safeIndex] ?? null;
  const hasGallery = images.length > 0;
  const hasPrices = priceGroups.length > 0;
  const imageCounter = images.length ? `${safeIndex + 1} / ${images.length}` : "";

  const showPrevious = useCallback(() => {
    if (images.length < 2) return;
    setSelectedIndex((current) =>
      (current - 1 + images.length) % images.length,
    );
  }, [images.length]);

  const showNext = useCallback(() => {
    if (images.length < 2) return;
    setSelectedIndex((current) => (current + 1) % images.length);
  }, [images.length]);

  // Активную миниатюру подкручиваем к центру полосы превью — прокручивается
  // только сама полоса. scrollIntoView двигал ещё и окно: на телефоне
  // страница проекта сразу после открытия съезжала вниз, к миниатюрам и ценам.
  useEffect(() => {
    const thumbnail = thumbnailRefs.current[safeIndex];
    const track = thumbnail?.parentElement;
    if (!thumbnail || !track) return;

    const trackBounds = track.getBoundingClientRect();
    const thumbnailBounds = thumbnail.getBoundingClientRect();
    track.scrollTo({
      left:
        track.scrollLeft +
        thumbnailBounds.left -
        trackBounds.left -
        (track.clientWidth - thumbnailBounds.width) / 2,
      behavior: "smooth",
    });
  }, [safeIndex]);

  function handleTouchStart(event: TouchEvent<HTMLDivElement>) {
    touchStartX.current = event.changedTouches[0]?.clientX ?? null;
  }

  function handleTouchEnd(event: TouchEvent<HTMLDivElement>) {
    if (touchStartX.current === null) return;

    const endX = event.changedTouches[0]?.clientX ?? touchStartX.current;
    const distance = endX - touchStartX.current;
    touchStartX.current = null;

    if (Math.abs(distance) < 45) return;
    if (distance > 0) showPrevious();
    else showNext();
  }

  function togglePriceGroup(title: string) {
    setOpenPriceGroups((current) => ({
      ...current,
      [title]: !current[title],
    }));
  }

  // Пропорции уже загруженных снимков — по ним решаем, как вписать кадр.
  const [imageRatios, setImageRatios] = useState<Record<string, number>>({});
  const activeRatio = activeImage ? imageRatios[activeImage.src] : undefined;
  // Снимок, близкий по пропорциям к сцене (рендеры 4:3–16:9, чертежи
  // фасадов), заполняет её целиком — без полос по краям: края чуть
  // обрезаются, а целиком кадр открывается по нажатию. Сильно вытянутый или
  // высокий кадр так обрезать нельзя — его показываем целиком на размытом
  // фоне из него же.
  const showWholeImage =
    activeRatio !== undefined && (activeRatio < 1.2 || activeRatio > 1.9);

  if (!hasGallery && !hasPrices) return null;

  return (
    <section
      className={`container section ${styles.section}`}
      id="prices"
      aria-label="Галерея проекта и цены по материалам"
    >
      <div
        className={`${styles.layout} ${
          !hasGallery || !hasPrices ? styles.singleColumn : ""
        }`}
      >
        {hasGallery && activeImage && (
          <div className={styles.galleryColumn}>
            <header className={styles.heading}>
              <p>Галерея</p>
              <h2>Изображения проекта</h2>
            </header>

            <div className={styles.viewerCard}>
              <div
                className={styles.mainStage}
                onTouchStart={handleTouchStart}
                onTouchEnd={handleTouchEnd}
              >
                {/* Вытянутый кадр показывается целиком, поля вокруг него
                    заполняет его же размытая копия — ей хватает крошечной
                    версии картинки. */}
                {showWholeImage && (
                  <Image
                    className={styles.stageBackdrop}
                    src={activeImage.src}
                    alt=""
                    fill
                    sizes="96px"
                  />
                )}
                <button
                  className={styles.mainImageButton}
                  type="button"
                  onClick={() => setLightboxOpen(true)}
                  aria-label={`Открыть изображение «${
                    activeImage.caption || activeImage.alt
                  }» на весь экран`}
                >
                  <Image
                    src={activeImage.src}
                    alt={activeImage.alt}
                    fill
                    sizes="(max-width: 980px) 100vw, 720px"
                    style={{ objectFit: showWholeImage ? "contain" : "cover" }}
                    priority
                    onLoad={(event) => {
                      const { naturalWidth, naturalHeight } = event.currentTarget;
                      const src = activeImage.src;
                      if (!naturalWidth || !naturalHeight) return;
                      setImageRatios((current) =>
                        src in current
                          ? current
                          : { ...current, [src]: naturalWidth / naturalHeight },
                      );
                    }}
                  />
                  <span className={styles.zoomBadge} aria-hidden="true">
                    <ExpandIcon />
                    <span className={styles.zoomLabel}>Увеличить</span>
                  </span>
                </button>

                {images.length > 1 && (
                  <>
                    <button
                      className={`${styles.stageArrow} ${styles.stageArrowLeft}`}
                      type="button"
                      onClick={showPrevious}
                      aria-label="Предыдущее изображение"
                    >
                      <ArrowLeftIcon />
                    </button>
                    <button
                      className={`${styles.stageArrow} ${styles.stageArrowRight}`}
                      type="button"
                      onClick={showNext}
                      aria-label="Следующее изображение"
                    >
                      <ArrowRightIcon />
                    </button>
                  </>
                )}

                <span className={styles.counter}>{imageCounter}</span>
              </div>

              <div className={styles.thumbnailArea}>
                <div className={styles.thumbnailTrack}>
                  {images.map((image, index) => {
                    const selected = index === safeIndex;

                    return (
                      <button
                        ref={(element) => {
                          thumbnailRefs.current[index] = element;
                        }}
                        className={`${styles.thumbnail} ${
                          selected ? styles.thumbnailActive : ""
                        }`}
                        key={`${image.id}-${image.src}`}
                        type="button"
                        onClick={() => setSelectedIndex(index)}
                        aria-current={selected ? "true" : undefined}
                        aria-label={`Показать: ${image.caption || image.alt}`}
                      >
                        <span className={styles.thumbnailImage}>
                          <Image
                            src={image.src}
                            alt=""
                            fill
                            sizes="120px"
                            style={{ objectFit: "cover" }}
                          />
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {hasPrices && (
          <aside className={styles.priceColumn}>
            {/* Примерная цена «всё вместе» — заголовком колонки цен: на
                телефоне это сразу под фото, на компьютере — сбоку от галереи.
                Отдельной плашкой её не ставим: колонка цен на компьютере
                фиксированной высоты, и лишний блок дал бы прокрутку внутри
                прайса. */}
            <header className={styles.heading}>
              {startingPrice ? (
                <>
                  <p>С фундаментом и кровлей</p>
                  <h2>от {startingPrice.total}</h2>
                  {/* ₽ — только в конце: так расшифровка помещается в одну
                      строку и на узком экране компьютера. */}
                  <span className={styles.headingNote}>
                    материалы {startingPrice.materials.replace(/\s*₽$/, "")} +
                    фундамент {startingPrice.foundation.replace(/\s*₽$/, "")} +
                    кровля {startingPrice.roof}
                  </span>
                </>
              ) : (
                <>
                  <p>Стоимость</p>
                  <h2>Цены по материалам</h2>
                </>
              )}
            </header>

            <div className={styles.pricePanel}>
              <div className={styles.priceList}>
                {priceGroups.map((group, groupIndex) => {
                  const isOpen = openPriceGroups[group.title] ?? true;
                  const contentId = `project-price-group-${groupIndex}`;

                  return (
                    <section className={styles.priceCard} key={group.title}>
                      <button
                        className={styles.priceCardHeader}
                        type="button"
                        onClick={() => togglePriceGroup(group.title)}
                        aria-expanded={isOpen}
                        aria-controls={contentId}
                      >
                        <span className={styles.materialIcon} aria-hidden="true">
                          <span />
                        </span>
                        <strong>{group.title}</strong>
                        <ChevronIcon open={isOpen} />
                      </button>

                      {isOpen && (
                        <div className={styles.priceRows} id={contentId}>
                          {group.items.map((item) => (
                            <div className={styles.priceRow} key={item.id}>
                              <span>{priceItemLabel(item.title, group.title)}</span>
                              <strong>{item.price}</strong>
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                  );
                })}
              </div>

              <div className={styles.priceFooter}>
                <p>
                  <span aria-hidden="true">i</span>
                  Цены в таблице — за комплект материалов. Стоимость под
                  ключ со сборкой и доставкой рассчитаем бесплатно.
                </p>
                <LeadFormButton
                  className={styles.calculateButton}
                  source="project_order"
                  projectSlug={projectSlug}
                  title="Узнать цену под ключ"
                >
                  <PhoneIcon />
                  Узнать цену под ключ
                </LeadFormButton>
              </div>
            </div>
          </aside>
        )}
      </div>

      {lightboxOpen && hasGallery && (
        <LightboxViewer
          images={images}
          activeIndex={safeIndex}
          onActiveIndexChange={setSelectedIndex}
          onClose={() => setLightboxOpen(false)}
        />
      )}
    </section>
  );
}
