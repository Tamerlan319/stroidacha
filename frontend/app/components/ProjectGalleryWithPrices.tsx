"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type TouchEvent,
} from "react";

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

function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m5 5 14 14M19 5 5 19" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

function MinusIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h14" />
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
  const [zoomLevel, setZoomLevel] = useState(1);
  const [stageViewport, setStageViewport] = useState({ width: 0, height: 0 });
  const [naturalImageSize, setNaturalImageSize] = useState({
    width: 0,
    height: 0,
  });
  const [openPriceGroups, setOpenPriceGroups] = useState<Record<string, boolean>>(
    () => Object.fromEntries(priceGroups.map((group) => [group.title, true])),
  );

  const thumbnailRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);
  const touchStartX = useRef<number | null>(null);
  const lightboxStageRef = useRef<HTMLDivElement | null>(null);

  const safeIndex = images.length
    ? Math.min(selectedIndex, images.length - 1)
    : 0;
  const activeImage = images[safeIndex] ?? null;

  const hasGallery = images.length > 0;
  const hasPrices = priceGroups.length > 0;

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

  const openLightbox = useCallback(() => {
    if (!activeImage) return;
    previouslyFocusedElement.current = document.activeElement as HTMLElement;
    setZoomLevel(1);
    setNaturalImageSize({ width: 0, height: 0 });
    setLightboxOpen(true);
  }, [activeImage]);

  const closeLightbox = useCallback(() => {
    setLightboxOpen(false);
    setZoomLevel(1);
  }, []);

  const imageCounter = useMemo(
    () => (images.length ? `${safeIndex + 1} / ${images.length}` : ""),
    [images.length, safeIndex],
  );

  const zoomPercent = `${Math.round(zoomLevel * 100)}%`;
  const canZoomIn = zoomLevel < 3;
  const canZoomOut = zoomLevel > 1;

  const lightboxImageStyle = useMemo<CSSProperties | undefined>(() => {
    if (
      !stageViewport.width ||
      !stageViewport.height ||
      !naturalImageSize.width ||
      !naturalImageSize.height
    ) {
      return undefined;
    }

    const containRatio = Math.min(
      stageViewport.width / naturalImageSize.width,
      stageViewport.height / naturalImageSize.height,
    );

    const baseWidth = Math.max(1, Math.floor(naturalImageSize.width * containRatio));
    const baseHeight = Math.max(1, Math.floor(naturalImageSize.height * containRatio));

    return {
      width: `${Math.round(baseWidth * zoomLevel)}px`,
      height: `${Math.round(baseHeight * zoomLevel)}px`,
    };
  }, [naturalImageSize.height, naturalImageSize.width, stageViewport.height, stageViewport.width, zoomLevel]);

  useEffect(() => {
    thumbnailRefs.current[safeIndex]?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
    });
  }, [safeIndex]);

  useEffect(() => {
    if (!lightboxOpen) return;

    setZoomLevel(1);
    setNaturalImageSize({ width: 0, height: 0 });
  }, [lightboxOpen, safeIndex]);

  useEffect(() => {
    if (!lightboxOpen) return;

    const stageElement = lightboxStageRef.current;
    if (!stageElement) return;

    const updateViewportSize = () => {
      const nextWidth = Math.max(1, stageElement.clientWidth - 24);
      const nextHeight = Math.max(1, stageElement.clientHeight - 24);
      setStageViewport({ width: nextWidth, height: nextHeight });
    };

    updateViewportSize();

    const resizeObserver = new ResizeObserver(updateViewportSize);
    resizeObserver.observe(stageElement);
    window.addEventListener("resize", updateViewportSize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updateViewportSize);
    };
  }, [lightboxOpen]);

  useEffect(() => {
    if (!lightboxOpen) return;

    const scrollY = window.scrollY;
    const previousHtmlOverflow = document.documentElement.style.overflow;
    const previousBodyOverflow = document.body.style.overflow;
    const previousBodyPosition = document.body.style.position;
    const previousBodyTop = document.body.style.top;
    const previousBodyWidth = document.body.style.width;
    const previousBodyLeft = document.body.style.left;
    const previousBodyRight = document.body.style.right;
    const previousBodyTouchAction = document.body.style.touchAction;

    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
    document.body.style.touchAction = "none";

    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeLightbox();
      }
      if (event.key === "ArrowLeft") {
        showPrevious();
      }
      if (event.key === "ArrowRight") {
        showNext();
      }
      if (event.key === "+" || event.key === "=") {
        setZoomLevel((current) => Math.min(3, Number((current + 0.25).toFixed(2))));
      }
      if (event.key === "-" || event.key === "_") {
        setZoomLevel((current) => Math.max(1, Number((current - 0.25).toFixed(2))));
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.documentElement.style.overflow = previousHtmlOverflow;
      document.body.style.overflow = previousBodyOverflow;
      document.body.style.position = previousBodyPosition;
      document.body.style.top = previousBodyTop;
      document.body.style.width = previousBodyWidth;
      document.body.style.left = previousBodyLeft;
      document.body.style.right = previousBodyRight;
      document.body.style.touchAction = previousBodyTouchAction;
      window.scrollTo(0, scrollY);
      previouslyFocusedElement.current?.focus();
    };
  }, [closeLightbox, lightboxOpen, showNext, showPrevious]);

  function selectImage(index: number) {
    setSelectedIndex(index);
  }

  function handleTouchStart(event: TouchEvent<HTMLDivElement>) {
    touchStartX.current = event.changedTouches[0]?.clientX ?? null;
  }

  function handleTouchEnd(event: TouchEvent<HTMLDivElement>) {
    if (touchStartX.current === null) return;
    if (lightboxOpen && zoomLevel > 1) {
      touchStartX.current = null;
      return;
    }

    const endX = event.changedTouches[0]?.clientX ?? touchStartX.current;
    const distance = endX - touchStartX.current;
    touchStartX.current = null;

    if (Math.abs(distance) < 45) return;
    if (distance > 0) showPrevious();
    else showNext();
  }

  function increaseZoom() {
    setZoomLevel((current) => Math.min(3, Number((current + 0.25).toFixed(2))));
  }

  function decreaseZoom() {
    setZoomLevel((current) => Math.max(1, Number((current - 0.25).toFixed(2))));
  }

  function toggleZoom() {
    setZoomLevel((current) => (current > 1 ? 1 : 2));
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
                  onClick={openLightbox}
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
                        onClick={() => selectImage(index)}
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

      {lightboxOpen && activeImage && (
        <div
          className={styles.lightboxOverlay}
          role="dialog"
          aria-modal="true"
          aria-label="Просмотр изображений проекта"
          onMouseDown={(event) => {
            if (event.currentTarget === event.target) closeLightbox();
          }}
        >
          <div
            className={styles.lightbox}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            onClick={(event) => event.stopPropagation()}
          >
            <div className={styles.lightboxTopbar}>
              <div className={styles.lightboxMeta}>
                <span>{imageCounter}</span>
                <strong>{activeImage.caption || "Изображение проекта"}</strong>
              </div>

              <div className={styles.lightboxToolbar}>
                <button
                  className={styles.lightboxZoomButton}
                  type="button"
                  onClick={decreaseZoom}
                  disabled={!canZoomOut}
                  aria-label="Уменьшить изображение"
                >
                  <MinusIcon />
                </button>
                <span className={styles.lightboxZoomValue}>{zoomPercent}</span>
                <button
                  className={styles.lightboxZoomButton}
                  type="button"
                  onClick={increaseZoom}
                  disabled={!canZoomIn}
                  aria-label="Увеличить изображение"
                >
                  <PlusIcon />
                </button>
                <button
                  ref={closeButtonRef}
                  className={styles.lightboxClose}
                  type="button"
                  onClick={closeLightbox}
                  aria-label="Закрыть просмотрщик"
                >
                  <CloseIcon />
                </button>
              </div>
            </div>

            <div className={styles.lightboxStage} ref={lightboxStageRef}>
              {images.length > 1 && (
                <button
                  className={`${styles.lightboxArrow} ${styles.lightboxArrowLeft}`}
                  type="button"
                  onClick={showPrevious}
                  aria-label="Предыдущее изображение"
                >
                  <ArrowLeftIcon />
                </button>
              )}

              <div className={styles.lightboxZoomCanvas}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  className={styles.lightboxStageImage}
                  src={activeImage.src}
                  alt={activeImage.alt}
                  style={lightboxImageStyle}
                  onLoad={(event) => {
                    setNaturalImageSize({
                      width: event.currentTarget.naturalWidth,
                      height: event.currentTarget.naturalHeight,
                    });
                  }}
                  onDoubleClick={toggleZoom}
                />
              </div>

              {images.length > 1 && (
                <button
                  className={`${styles.lightboxArrow} ${styles.lightboxArrowRight}`}
                  type="button"
                  onClick={showNext}
                  aria-label="Следующее изображение"
                >
                  <ArrowRightIcon />
                </button>
              )}

              <span className={styles.lightboxFloatingCounter}>{imageCounter}</span>
            </div>

            {images.length > 1 && (
              <div className={styles.lightboxThumbnails}>
                {images.map((image, index) => (
                  <button
                    className={`${styles.lightboxThumbnail} ${
                      index === safeIndex ? styles.lightboxThumbnailActive : ""
                    }`}
                    key={`lightbox-${image.id}-${image.src}`}
                    type="button"
                    onClick={() => selectImage(index)}
                    aria-label={`Открыть: ${image.caption || image.alt}`}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={image.src} alt="" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
