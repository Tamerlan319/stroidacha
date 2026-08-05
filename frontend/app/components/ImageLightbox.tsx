"use client";

import {
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

import styles from "./ImageLightbox.module.css";

export type LightboxImage = {
  id: string | number;
  src: string;
  alt: string;
  caption?: string;
};

type ImageLightboxProps = {
  images: LightboxImage[];
  previewLimit?: number;
  className?: string;
};

type PointerStart = {
  x: number;
  y: number;
  time: number;
};

const HORIZONTAL_SWIPE_DISTANCE = 48;
const VERTICAL_CLOSE_DISTANCE = 90;
const SWIPE_MAX_DURATION = 700;

export default function ImageLightbox({
  images,
  previewLimit = 5,
  className = "",
}: ImageLightboxProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const pointerStartRef = useRef<PointerStart | null>(null);
  const ignoreNextOverlayClickRef = useRef(false);

  const activeImage =
    activeIndex !== null && images[activeIndex] ? images[activeIndex] : null;

  const previewImages = images.slice(0, previewLimit);
  const hiddenCount = Math.max(images.length - previewImages.length, 0);

  const openImage = useCallback((index: number) => {
    setActiveIndex(index);
  }, []);

  const closeImage = useCallback(() => {
    setActiveIndex(null);
  }, []);

  const showPrevious = useCallback(() => {
    setActiveIndex((currentIndex) => {
      if (currentIndex === null || images.length === 0) {
        return null;
      }

      return (currentIndex - 1 + images.length) % images.length;
    });
  }, [images.length]);

  const showNext = useCallback(() => {
    setActiveIndex((currentIndex) => {
      if (currentIndex === null || images.length === 0) {
        return null;
      }

      return (currentIndex + 1) % images.length;
    });
  }, [images.length]);

  useEffect(() => {
    if (activeIndex === null) {
      return;
    }

    const body = document.body;
    const html = document.documentElement;
    const scrollY = window.scrollY;
    const previouslyFocusedElement =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;

    const previousBodyStyles = {
      position: body.style.position,
      top: body.style.top,
      right: body.style.right,
      bottom: body.style.bottom,
      left: body.style.left,
      width: body.style.width,
      height: body.style.height,
      overflow: body.style.overflow,
      touchAction: body.style.touchAction,
      overscrollBehavior: body.style.overscrollBehavior,
    };

    const previousHtmlStyles = {
      overflow: html.style.overflow,
      height: html.style.height,
      touchAction: html.style.touchAction,
      overscrollBehavior: html.style.overscrollBehavior,
      scrollBehavior: html.style.scrollBehavior,
    };

    body.style.position = "fixed";
    body.style.top = `-${scrollY}px`;
    body.style.right = "0";
    body.style.bottom = "0";
    body.style.left = "0";
    body.style.width = "100%";
    body.style.height = "100%";
    body.style.overflow = "hidden";
    body.style.touchAction = "none";
    body.style.overscrollBehavior = "none";

    html.style.overflow = "hidden";
    html.style.height = "100%";
    html.style.touchAction = "none";
    html.style.overscrollBehavior = "none";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeImage();
        return;
      }

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        showPrevious();
        return;
      }

      if (event.key === "ArrowRight") {
        event.preventDefault();
        showNext();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    const focusFrame = window.requestAnimationFrame(() => {
      closeButtonRef.current?.focus({ preventScroll: true });
    });

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      window.cancelAnimationFrame(focusFrame);

      body.style.position = previousBodyStyles.position;
      body.style.top = previousBodyStyles.top;
      body.style.right = previousBodyStyles.right;
      body.style.bottom = previousBodyStyles.bottom;
      body.style.left = previousBodyStyles.left;
      body.style.width = previousBodyStyles.width;
      body.style.height = previousBodyStyles.height;
      body.style.overflow = previousBodyStyles.overflow;
      body.style.touchAction = previousBodyStyles.touchAction;
      body.style.overscrollBehavior =
        previousBodyStyles.overscrollBehavior;

      html.style.overflow = previousHtmlStyles.overflow;
      html.style.height = previousHtmlStyles.height;
      html.style.touchAction = previousHtmlStyles.touchAction;
      html.style.overscrollBehavior =
        previousHtmlStyles.overscrollBehavior;

      html.style.scrollBehavior = "auto";
      window.scrollTo(0, scrollY);
      html.style.scrollBehavior = previousHtmlStyles.scrollBehavior;

      previouslyFocusedElement?.focus({ preventScroll: true });
    };
  }, [activeIndex, closeImage, showNext, showPrevious]);

  useEffect(() => {
    if (
      activeIndex === null ||
      images.length < 2 ||
      typeof window === "undefined"
    ) {
      return;
    }

    const previousIndex =
      (activeIndex - 1 + images.length) % images.length;
    const nextIndex = (activeIndex + 1) % images.length;

    [images[previousIndex], images[nextIndex]].forEach((image) => {
      if (!image) {
        return;
      }

      const preloadedImage = new window.Image();
      preloadedImage.src = image.src;
    });
  }, [activeIndex, images]);

  function handlePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    const target = event.target;

    if (
      target instanceof Element &&
      target.closest("button, a")
    ) {
      pointerStartRef.current = null;
      return;
    }

    pointerStartRef.current = {
      x: event.clientX,
      y: event.clientY,
      time: Date.now(),
    };

    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function handlePointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    const pointerStart = pointerStartRef.current;
    pointerStartRef.current = null;

    if (!pointerStart) {
      return;
    }

    const deltaX = event.clientX - pointerStart.x;
    const deltaY = event.clientY - pointerStart.y;
    const absoluteX = Math.abs(deltaX);
    const absoluteY = Math.abs(deltaY);
    const duration = Date.now() - pointerStart.time;

    if (
      duration <= SWIPE_MAX_DURATION &&
      absoluteX >= HORIZONTAL_SWIPE_DISTANCE &&
      absoluteX > absoluteY * 1.15
    ) {
      ignoreNextOverlayClickRef.current = true;

      if (deltaX < 0) {
        showNext();
      } else {
        showPrevious();
      }

      return;
    }

    if (
      duration <= SWIPE_MAX_DURATION &&
      deltaY >= VERTICAL_CLOSE_DISTANCE &&
      absoluteY > absoluteX * 1.15
    ) {
      ignoreNextOverlayClickRef.current = true;
      closeImage();
      return;
    }

    if (absoluteX > 10 || absoluteY > 10) {
      ignoreNextOverlayClickRef.current = true;
    }
  }

  function handlePointerCancel() {
    pointerStartRef.current = null;
  }

  function handleOverlayClick(event: MouseEvent<HTMLDivElement>) {
    if (ignoreNextOverlayClickRef.current) {
      ignoreNextOverlayClickRef.current = false;
      return;
    }

    if (event.defaultPrevented) {
      return;
    }

    closeImage();
  }

  if (images.length === 0) {
    return null;
  }

  const lightbox =
    activeImage && typeof document !== "undefined" ? (
      <div
        className={styles.overlay}
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-lightbox-title"
        onClick={handleOverlayClick}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
      >
        <h2 id="project-lightbox-title" className={styles.srOnly}>
          Просмотр фотографий проекта
        </h2>

        <button
          ref={closeButtonRef}
          className={styles.closeButton}
          type="button"
          aria-label="Закрыть просмотр фотографий"
          onClick={(event) => {
            event.stopPropagation();
            closeImage();
          }}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6 18 18M18 6 6 18" />
          </svg>
        </button>

        <div className={styles.stage}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className={styles.image}
            src={activeImage.src}
            alt={activeImage.alt}
            draggable={false}
            onClick={(event) => event.stopPropagation()}
          />
        </div>

        {images.length > 1 && (
          <>
            <button
              className={`${styles.arrowButton} ${styles.previousButton}`}
              type="button"
              aria-label="Показать предыдущее изображение"
              onClick={(event) => {
                event.stopPropagation();
                showPrevious();
              }}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m15 5-7 7 7 7" />
              </svg>
            </button>

            <button
              className={`${styles.arrowButton} ${styles.nextButton}`}
              type="button"
              aria-label="Показать следующее изображение"
              onClick={(event) => {
                event.stopPropagation();
                showNext();
              }}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m9 5 7 7-7 7" />
              </svg>
            </button>
          </>
        )}

        <div
          className={styles.bottomBar}
          onClick={(event) => event.stopPropagation()}
        >
          {activeImage.caption && (
            <span className={styles.caption}>{activeImage.caption}</span>
          )}

          <span className={styles.counter}>
            {(activeIndex ?? 0) + 1} / {images.length}
          </span>
        </div>
      </div>
    ) : null;

  return (
    <>
      <div className={`projectGallery projectGalleryCompact ${className}`}>
        {previewImages.map((image, index) => {
          const isLastPreview =
            hiddenCount > 0 && index === previewImages.length - 1;

          return (
            <button
              className={`galleryItem ${
                index === 0 ? "galleryItemLarge" : ""
              }`}
              key={image.id}
              type="button"
              onClick={() => openImage(index)}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={image.src} alt={image.alt} />

              {image.caption && <span>{image.caption}</span>}

              {isLastPreview && (
                <div className="galleryMore">
                  <strong>+{hiddenCount}</strong>
                  <small>Смотреть все фото</small>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {lightbox ? createPortal(lightbox, document.body) : null}
    </>
  );
}
