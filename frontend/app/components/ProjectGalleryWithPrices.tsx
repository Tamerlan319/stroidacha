"use client";

import { useCallback, useEffect, useRef, useState, type TouchEvent } from "react";

import ProjectGalleryLightbox from "./ProjectGalleryLightbox";
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

type ProjectGalleryWithPricesProps = {
  images: ProjectMediaItem[];
  priceGroups: ProjectPriceGroup[];
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
      <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" />
      <path d="m3 8 6-6M21 8l-6-6M3 16l6 6M21 16l-6 6" />
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

export default function ProjectGalleryWithPrices({
  images,
  priceGroups,
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

  useEffect(() => {
    thumbnailRefs.current[safeIndex]?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
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
                <button
                  className={styles.mainImageButton}
                  type="button"
                  onClick={() => setLightboxOpen(true)}
                  aria-label={`Открыть изображение «${
                    activeImage.caption || activeImage.alt
                  }» на весь экран`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={activeImage.src} alt={activeImage.alt} />
                  <span className={styles.zoomBadge}>
                    <ExpandIcon />
                    Увеличить
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
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={image.src} alt="" />
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
            <header className={styles.heading}>
              <p>Стоимость</p>
              <h2>Цены по материалам</h2>
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
                              <span>{item.title}</span>
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
                  Стоимость указана за комплект материалов. Итог зависит от
                  комплектации, фундамента, кровли и доставки.
                </p>
                <a className={styles.calculateButton} href="#lead-form">
                  <PhoneIcon />
                  Получить точный расчёт
                </a>
              </div>
            </div>
          </aside>
        )}
      </div>

      {lightboxOpen && hasGallery && (
        <ProjectGalleryLightbox
          images={images}
          activeIndex={safeIndex}
          onActiveIndexChange={setSelectedIndex}
          onClose={() => setLightboxOpen(false)}
        />
      )}
    </section>
  );
}
