"use client";

import {
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
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

type Point = {
  x: number;
  y: number;
};

type PointerStart = Point & {
  time: number;
};

type PinchStart = {
  distance: number;
  center: Point;
  scale: number;
  offset: Point;
};

const MIN_SCALE = 1;
const MAX_SCALE = 5;
const ZOOM_STEP = 0.5;
const DOUBLE_TAP_SCALE = 2.5;
const HORIZONTAL_SWIPE_DISTANCE = 48;
const VERTICAL_CLOSE_DISTANCE = 90;
const SWIPE_MAX_DURATION = 700;
const TAP_MAX_DISTANCE = 12;
const DOUBLE_TAP_DELAY = 320;

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

function getDistance(first: Point, second: Point) {
  return Math.hypot(second.x - first.x, second.y - first.y);
}

function getCenter(first: Point, second: Point): Point {
  return {
    x: (first.x + second.x) / 2,
    y: (first.y + second.y) / 2,
  };
}

export default function ImageLightbox({
  images,
  previewLimit = 5,
  className = "",
}: ImageLightboxProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [scale, setScale] = useState(MIN_SCALE);
  const [offset, setOffset] = useState<Point>({ x: 0, y: 0 });

  const stageRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const scaleRef = useRef(scale);
  const offsetRef = useRef(offset);
  const pointersRef = useRef<Map<number, Point>>(new Map());
  const pointerStartRef = useRef<PointerStart | null>(null);
  const panLastPointRef = useRef<Point | null>(null);
  const pinchStartRef = useRef<PinchStart | null>(null);
  const ignoreNextOverlayClickRef = useRef(false);
  const lastTapRef = useRef<PointerStart | null>(null);

  const activeImage =
    activeIndex !== null && images[activeIndex] ? images[activeIndex] : null;
  const previewImages = images.slice(0, previewLimit);
  const hiddenCount = Math.max(images.length - previewImages.length, 0);

  useEffect(() => {
    scaleRef.current = scale;
  }, [scale]);

  useEffect(() => {
    offsetRef.current = offset;
  }, [offset]);

  const getClampedOffset = useCallback(
    (nextOffset: Point, nextScale = scaleRef.current): Point => {
      const stage = stageRef.current;
      const image = imageRef.current;

      if (!stage || !image || nextScale <= MIN_SCALE) {
        return { x: 0, y: 0 };
      }

      const displayedWidth = image.offsetWidth;
      const displayedHeight = image.offsetHeight;
      const stageWidth = stage.clientWidth;
      const stageHeight = stage.clientHeight;

      const maximumX = Math.max(
        0,
        (displayedWidth * nextScale - stageWidth) / 2,
      );
      const maximumY = Math.max(
        0,
        (displayedHeight * nextScale - stageHeight) / 2,
      );

      return {
        x: clamp(nextOffset.x, -maximumX, maximumX),
        y: clamp(nextOffset.y, -maximumY, maximumY),
      };
    },
    [],
  );

  const applyZoom = useCallback(
    (nextScale: number, focalPoint?: Point) => {
      const clampedScale = clamp(nextScale, MIN_SCALE, MAX_SCALE);
      const currentScale = scaleRef.current;
      const currentOffset = offsetRef.current;

      if (clampedScale === MIN_SCALE) {
        const zeroOffset = { x: 0, y: 0 };
        scaleRef.current = MIN_SCALE;
        offsetRef.current = zeroOffset;
        setScale(MIN_SCALE);
        setOffset(zeroOffset);
        return;
      }

      let nextOffset = currentOffset;

      if (focalPoint && stageRef.current && currentScale > 0) {
        const stageBounds = stageRef.current.getBoundingClientRect();
        const pointFromCenter = {
          x:
            focalPoint.x -
            (stageBounds.left + stageBounds.width / 2) -
            currentOffset.x,
          y:
            focalPoint.y -
            (stageBounds.top + stageBounds.height / 2) -
            currentOffset.y,
        };
        const zoomRatio = clampedScale / currentScale;

        nextOffset = {
          x: currentOffset.x - pointFromCenter.x * (zoomRatio - 1),
          y: currentOffset.y - pointFromCenter.y * (zoomRatio - 1),
        };
      }

      const clampedOffset = getClampedOffset(nextOffset, clampedScale);
      scaleRef.current = clampedScale;
      offsetRef.current = clampedOffset;
      setScale(clampedScale);
      setOffset(clampedOffset);
    },
    [getClampedOffset],
  );

  const resetZoom = useCallback(() => {
    applyZoom(MIN_SCALE);
  }, [applyZoom]);

  const resetInteractionState = useCallback(() => {
    const zeroOffset = { x: 0, y: 0 };

    scaleRef.current = MIN_SCALE;
    offsetRef.current = zeroOffset;
    setScale(MIN_SCALE);
    setOffset(zeroOffset);

    pointersRef.current.clear();
    pointerStartRef.current = null;
    panLastPointRef.current = null;
    pinchStartRef.current = null;
    lastTapRef.current = null;
    ignoreNextOverlayClickRef.current = false;
  }, []);

  const openImage = useCallback(
    (index: number) => {
      resetInteractionState();
      setActiveIndex(index);
    },
    [resetInteractionState],
  );

  const closeImage = useCallback(() => {
    setActiveIndex(null);
  }, []);

  const showPrevious = useCallback(() => {
    if (images.length < 2) return;

    resetInteractionState();
    setActiveIndex((currentIndex) => {
      if (currentIndex === null) return null;
      return (currentIndex - 1 + images.length) % images.length;
    });
  }, [images.length, resetInteractionState]);

  const showNext = useCallback(() => {
    if (images.length < 2) return;

    resetInteractionState();
    setActiveIndex((currentIndex) => {
      if (currentIndex === null) return null;
      return (currentIndex + 1) % images.length;
    });
  }, [images.length, resetInteractionState]);

  useEffect(() => {
    if (activeIndex === null) return;

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

      if (event.key === "ArrowLeft" && scaleRef.current === MIN_SCALE) {
        event.preventDefault();
        showPrevious();
        return;
      }

      if (event.key === "ArrowRight" && scaleRef.current === MIN_SCALE) {
        event.preventDefault();
        showNext();
        return;
      }

      if (event.key === "+" || event.key === "=") {
        event.preventDefault();
        applyZoom(scaleRef.current + ZOOM_STEP);
        return;
      }

      if (event.key === "-") {
        event.preventDefault();
        applyZoom(scaleRef.current - ZOOM_STEP);
        return;
      }

      if (event.key === "0") {
        event.preventDefault();
        resetZoom();
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
      body.style.overscrollBehavior = previousBodyStyles.overscrollBehavior;

      html.style.overflow = previousHtmlStyles.overflow;
      html.style.height = previousHtmlStyles.height;
      html.style.touchAction = previousHtmlStyles.touchAction;
      html.style.overscrollBehavior = previousHtmlStyles.overscrollBehavior;
      html.style.scrollBehavior = "auto";
      window.scrollTo(0, scrollY);
      html.style.scrollBehavior = previousHtmlStyles.scrollBehavior;
      previouslyFocusedElement?.focus({ preventScroll: true });
    };
  }, [
    activeIndex,
    applyZoom,
    closeImage,
    resetZoom,
    showNext,
    showPrevious,
  ]);

  useEffect(() => {
    if (
      activeIndex === null ||
      images.length < 2 ||
      typeof window === "undefined"
    ) {
      return;
    }

    const previousIndex = (activeIndex - 1 + images.length) % images.length;
    const nextIndex = (activeIndex + 1) % images.length;

    [images[previousIndex], images[nextIndex]].forEach((image) => {
      if (!image) return;
      const preloadedImage = new window.Image();
      preloadedImage.src = image.src;
    });
  }, [activeIndex, images]);

  useEffect(() => {
    function clampAfterResize() {
      const clampedOffset = getClampedOffset(
        offsetRef.current,
        scaleRef.current,
      );
      offsetRef.current = clampedOffset;
      setOffset(clampedOffset);
    }

    window.addEventListener("resize", clampAfterResize);
    return () => window.removeEventListener("resize", clampAfterResize);
  }, [getClampedOffset]);

  function handlePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    const target = event.target;

    if (target instanceof Element && target.closest("button, a")) {
      return;
    }

    const point = { x: event.clientX, y: event.clientY };
    pointersRef.current.set(event.pointerId, point);
    event.currentTarget.setPointerCapture?.(event.pointerId);

    if (pointersRef.current.size === 1) {
      pointerStartRef.current = { ...point, time: Date.now() };
      panLastPointRef.current = point;
      pinchStartRef.current = null;
      return;
    }

    if (pointersRef.current.size === 2) {
      const [firstPoint, secondPoint] = Array.from(
        pointersRef.current.values(),
      );

      pinchStartRef.current = {
        distance: getDistance(firstPoint, secondPoint),
        center: getCenter(firstPoint, secondPoint),
        scale: scaleRef.current,
        offset: offsetRef.current,
      };
      pointerStartRef.current = null;
      panLastPointRef.current = null;
      ignoreNextOverlayClickRef.current = true;
    }
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    if (!pointersRef.current.has(event.pointerId)) return;

    const point = { x: event.clientX, y: event.clientY };
    pointersRef.current.set(event.pointerId, point);

    if (pointersRef.current.size === 2 && pinchStartRef.current) {
      const [firstPoint, secondPoint] = Array.from(
        pointersRef.current.values(),
      );
      const currentDistance = getDistance(firstPoint, secondPoint);
      const currentCenter = getCenter(firstPoint, secondPoint);
      const pinchStart = pinchStartRef.current;

      if (pinchStart.distance <= 0) return;

      const nextScale = clamp(
        pinchStart.scale * (currentDistance / pinchStart.distance),
        MIN_SCALE,
        MAX_SCALE,
      );
      const stageBounds = stageRef.current?.getBoundingClientRect();
      let nextOffset = {
        x: pinchStart.offset.x + (currentCenter.x - pinchStart.center.x),
        y: pinchStart.offset.y + (currentCenter.y - pinchStart.center.y),
      };

      if (stageBounds && pinchStart.scale > 0) {
        const pointFromCenter = {
          x:
            pinchStart.center.x -
            (stageBounds.left + stageBounds.width / 2) -
            pinchStart.offset.x,
          y:
            pinchStart.center.y -
            (stageBounds.top + stageBounds.height / 2) -
            pinchStart.offset.y,
        };
        const zoomRatio = nextScale / pinchStart.scale;

        nextOffset = {
          x: nextOffset.x - pointFromCenter.x * (zoomRatio - 1),
          y: nextOffset.y - pointFromCenter.y * (zoomRatio - 1),
        };
      }

      const clampedOffset = getClampedOffset(nextOffset, nextScale);
      scaleRef.current = nextScale;
      offsetRef.current = clampedOffset;
      setScale(nextScale);
      setOffset(clampedOffset);
      return;
    }

    if (
      pointersRef.current.size === 1 &&
      scaleRef.current > MIN_SCALE &&
      panLastPointRef.current
    ) {
      const delta = {
        x: point.x - panLastPointRef.current.x,
        y: point.y - panLastPointRef.current.y,
      };
      const nextOffset = getClampedOffset({
        x: offsetRef.current.x + delta.x,
        y: offsetRef.current.y + delta.y,
      });

      panLastPointRef.current = point;
      offsetRef.current = nextOffset;
      setOffset(nextOffset);
      ignoreNextOverlayClickRef.current = true;
    }
  }

  function handlePointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    const releasedPoint = pointersRef.current.get(event.pointerId);
    const pointerStart = pointerStartRef.current;

    pointersRef.current.delete(event.pointerId);

    if (pointersRef.current.size === 1) {
      const [remainingPoint] = Array.from(pointersRef.current.values());
      panLastPointRef.current = remainingPoint;
      pointerStartRef.current = {
        ...remainingPoint,
        time: Date.now(),
      };
      pinchStartRef.current = null;
      return;
    }

    panLastPointRef.current = null;
    pinchStartRef.current = null;

    if (!pointerStart || !releasedPoint) {
      pointerStartRef.current = null;
      return;
    }

    pointerStartRef.current = null;

    const deltaX = releasedPoint.x - pointerStart.x;
    const deltaY = releasedPoint.y - pointerStart.y;
    const absoluteX = Math.abs(deltaX);
    const absoluteY = Math.abs(deltaY);
    const duration = Date.now() - pointerStart.time;
    const movedDistance = Math.hypot(deltaX, deltaY);

    if (movedDistance <= TAP_MAX_DISTANCE && duration <= 260) {
      const lastTap = lastTapRef.current;
      const isDoubleTap =
        lastTap !== null &&
        Date.now() - lastTap.time <= DOUBLE_TAP_DELAY &&
        Math.hypot(
          releasedPoint.x - lastTap.x,
          releasedPoint.y - lastTap.y,
        ) <= 36;

      if (isDoubleTap) {
        if (scaleRef.current > MIN_SCALE) {
          resetZoom();
        } else {
          applyZoom(DOUBLE_TAP_SCALE, releasedPoint);
        }
        lastTapRef.current = null;
        ignoreNextOverlayClickRef.current = true;
        return;
      }

      lastTapRef.current = { ...releasedPoint, time: Date.now() };
    }

    if (scaleRef.current > MIN_SCALE) return;

    if (
      duration <= SWIPE_MAX_DURATION &&
      absoluteX >= HORIZONTAL_SWIPE_DISTANCE &&
      absoluteX > absoluteY * 1.15
    ) {
      ignoreNextOverlayClickRef.current = true;
      if (deltaX < 0) showNext();
      else showPrevious();
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

    if (movedDistance > TAP_MAX_DISTANCE) {
      ignoreNextOverlayClickRef.current = true;
    }
  }

  function handlePointerCancel(event: ReactPointerEvent<HTMLDivElement>) {
    pointersRef.current.delete(event.pointerId);
    pointerStartRef.current = null;
    panLastPointRef.current = null;
    pinchStartRef.current = null;
  }

  function handleOverlayClick(event: MouseEvent<HTMLDivElement>) {
    if (ignoreNextOverlayClickRef.current) {
      ignoreNextOverlayClickRef.current = false;
      return;
    }

    if (event.defaultPrevented) return;
    closeImage();
  }

  function handleWheel(event: ReactWheelEvent<HTMLDivElement>) {
    event.preventDefault();
    const zoomDelta = event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;

    applyZoom(scaleRef.current + zoomDelta, {
      x: event.clientX,
      y: event.clientY,
    });
  }

  if (images.length === 0) return null;

  const lightbox =
    activeImage && typeof document !== "undefined" ? (
      <div
        className={styles.overlay}
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-lightbox-title"
        onClick={handleOverlayClick}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
        onWheel={handleWheel}
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

        <div ref={stageRef} className={styles.stage}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            ref={imageRef}
            className={styles.image}
            src={activeImage.src}
            alt={activeImage.alt}
            draggable={false}
            style={{
              transform: `translate3d(${offset.x}px, ${offset.y}px, 0) scale(${scale})`,
              cursor: scale > MIN_SCALE ? "grab" : "zoom-in",
            }}
            onClick={(event) => event.stopPropagation()}
            onDoubleClick={(event) => {
              event.stopPropagation();
              if (scaleRef.current > MIN_SCALE) {
                resetZoom();
              } else {
                applyZoom(DOUBLE_TAP_SCALE, {
                  x: event.clientX,
                  y: event.clientY,
                });
              }
            }}
          />
        </div>

        {images.length > 1 && scale === MIN_SCALE && (
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
          className={styles.zoomControls}
          onClick={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            aria-label="Уменьшить фотографию"
            disabled={scale <= MIN_SCALE}
            onClick={() => applyZoom(scaleRef.current - ZOOM_STEP)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 12h12" />
            </svg>
          </button>
          <button
            className={styles.zoomValue}
            type="button"
            aria-label="Вернуть исходный размер фотографии"
            disabled={scale <= MIN_SCALE}
            onClick={resetZoom}
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            type="button"
            aria-label="Увеличить фотографию"
            disabled={scale >= MAX_SCALE}
            onClick={() => applyZoom(scaleRef.current + ZOOM_STEP)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 6v12M6 12h12" />
            </svg>
          </button>
        </div>

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
