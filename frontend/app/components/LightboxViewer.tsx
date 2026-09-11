"use client";

import {
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

import styles from "./LightboxViewer.module.css";

// Единый полноэкранный просмотр картинок: галерея проекта
// (ProjectGalleryWithPrices), планировки и портфолио (ImageLightbox). Раньше
// это были две почти одинаковые копии по ~700 строк — любое исправление
// приходилось вносить дважды.

export type LightboxImage = {
  id: string | number;
  src: string;
  alt: string;
  caption?: string;
};

type LightboxViewerProps = {
  images: LightboxImage[];
  activeIndex: number;
  onActiveIndexChange: (index: number) => void;
  onClose: () => void;
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
const CLICK_ZOOM_SCALE = 2.5;
// Щипок или Ctrl+колесо почти до исходного размера — считаем, что человек
// хотел вернуться к целой картинке, а не застрять на 103% без стрелок.
const SNAP_TO_FIT_SCALE = 1.05;
const WHEEL_ZOOM_SPEED = 0.0025;
const KEYBOARD_PAN_STEP = 80;
const HORIZONTAL_SWIPE_DISTANCE = 48;
const VERTICAL_CLOSE_DISTANCE = 90;
const SWIPE_MAX_DURATION = 700;
const TAP_MAX_DISTANCE = 12;
const TAP_MAX_DURATION = 260;
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

export default function LightboxViewer({
  images,
  activeIndex,
  onActiveIndexChange,
  onClose,
}: LightboxViewerProps) {
  const [scale, setScale] = useState(MIN_SCALE);
  const [offset, setOffset] = useState<Point>({ x: 0, y: 0 });
  const [isGesturing, setIsGesturing] = useState(false);
  const titleId = useId();

  const overlayRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const scaleRef = useRef(scale);
  const offsetRef = useRef(offset);
  const pointersRef = useRef<Map<number, Point>>(new Map());
  const pointerStartRef = useRef<PointerStart | null>(null);
  const pointerStartedOnImageRef = useRef(false);
  const panLastPointRef = useRef<Point | null>(null);
  const pinchStartRef = useRef<PinchStart | null>(null);
  const ignoreNextOverlayClickRef = useRef(false);
  const lastTapRef = useRef<PointerStart | null>(null);

  // Родитель передаёт onClose/onActiveIndexChange стрелочными функциями —
  // новыми на каждый рендер. Держим последние в ref, иначе эффекты ниже
  // (блокировка прокрутки страницы, клавиатура) перезапускались бы при
  // каждом перелистывании: страница под просмотром дёргалась, а фокус
  // прыгал на крестик.
  const onCloseRef = useRef(onClose);
  const onActiveIndexChangeRef = useRef(onActiveIndexChange);

  const safeIndex = images.length
    ? Math.min(Math.max(activeIndex, 0), images.length - 1)
    : 0;
  const safeIndexRef = useRef(safeIndex);
  const activeImage = images[safeIndex] ?? null;

  useEffect(() => {
    onCloseRef.current = onClose;
    onActiveIndexChangeRef.current = onActiveIndexChange;
  }, [onClose, onActiveIndexChange]);

  useEffect(() => {
    safeIndexRef.current = safeIndex;
  }, [safeIndex]);

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

      const maximumX = Math.max(
        0,
        (image.offsetWidth * nextScale - stage.clientWidth) / 2,
      );
      const maximumY = Math.max(
        0,
        (image.offsetHeight * nextScale - stage.clientHeight) / 2,
      );

      return {
        x: clamp(nextOffset.x, -maximumX, maximumX),
        y: clamp(nextOffset.y, -maximumY, maximumY),
      };
    },
    [],
  );

  const commitView = useCallback((nextScale: number, nextOffset: Point) => {
    scaleRef.current = nextScale;
    offsetRef.current = nextOffset;
    setScale(nextScale);
    setOffset(nextOffset);
  }, []);

  const applyZoom = useCallback(
    (nextScale: number, focalPoint?: Point) => {
      const clampedScale = clamp(nextScale, MIN_SCALE, MAX_SCALE);
      const currentScale = scaleRef.current;
      const currentOffset = offsetRef.current;

      if (clampedScale < SNAP_TO_FIT_SCALE) {
        commitView(MIN_SCALE, { x: 0, y: 0 });
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

      commitView(clampedScale, getClampedOffset(nextOffset, clampedScale));
    },
    [commitView, getClampedOffset],
  );

  const resetZoom = useCallback(() => {
    commitView(MIN_SCALE, { x: 0, y: 0 });
  }, [commitView]);

  const toggleZoom = useCallback(
    (point: Point) => {
      if (scaleRef.current > MIN_SCALE) {
        resetZoom();
      } else {
        applyZoom(CLICK_ZOOM_SCALE, point);
      }
    },
    [applyZoom, resetZoom],
  );

  // Сдвиг увеличенной картинки — колесом, стрелками, перетаскиванием.
  // Картинка целиком помещается в окно, пока не увеличена, так что двигать
  // её имеет смысл только при масштабе больше 100%.
  const panBy = useCallback(
    (deltaX: number, deltaY: number) => {
      if (scaleRef.current <= MIN_SCALE) return;

      const nextOffset = getClampedOffset({
        x: offsetRef.current.x + deltaX,
        y: offsetRef.current.y + deltaY,
      });

      offsetRef.current = nextOffset;
      setOffset(nextOffset);
    },
    [getClampedOffset],
  );

  const resetInteractionState = useCallback(() => {
    commitView(MIN_SCALE, { x: 0, y: 0 });
    pointersRef.current.clear();
    pointerStartRef.current = null;
    pointerStartedOnImageRef.current = false;
    panLastPointRef.current = null;
    pinchStartRef.current = null;
    lastTapRef.current = null;
    ignoreNextOverlayClickRef.current = false;
    setIsGesturing(false);
  }, [commitView]);

  const showPrevious = useCallback(() => {
    if (images.length < 2) return;
    resetInteractionState();
    onActiveIndexChangeRef.current(
      (safeIndexRef.current - 1 + images.length) % images.length,
    );
  }, [images.length, resetInteractionState]);

  const showNext = useCallback(() => {
    if (images.length < 2) return;
    resetInteractionState();
    onActiveIndexChangeRef.current((safeIndexRef.current + 1) % images.length);
  }, [images.length, resetInteractionState]);

  const close = useCallback(() => {
    onCloseRef.current();
  }, []);

  // Блокировка прокрутки страницы под просмотром — один раз на открытие.
  useEffect(() => {
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

    const focusFrame = window.requestAnimationFrame(() => {
      closeButtonRef.current?.focus({ preventScroll: true });
    });

    return () => {
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
  }, []);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }

      if (event.key.startsWith("Arrow") && scaleRef.current > MIN_SCALE) {
        event.preventDefault();
        panBy(
          event.key === "ArrowLeft"
            ? KEYBOARD_PAN_STEP
            : event.key === "ArrowRight"
              ? -KEYBOARD_PAN_STEP
              : 0,
          event.key === "ArrowUp"
            ? KEYBOARD_PAN_STEP
            : event.key === "ArrowDown"
              ? -KEYBOARD_PAN_STEP
              : 0,
        );
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
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [applyZoom, close, panBy, resetZoom, showNext, showPrevious]);

  // Колесо: у увеличенной картинки — прокрутка (двумя пальцами по тачпаду
  // тоже), Ctrl/⌘ + колесо и щипок на тачпаде — масштаб. Раньше колесо
  // всегда меняло масштаб, и увеличенную картинку нельзя было «прокрутить».
  // Слушатель нативный и не пассивный: React вешает onWheel пассивным, а без
  // preventDefault Ctrl+колесо масштабирует всю страницу браузера.
  useEffect(() => {
    const overlay = overlayRef.current;
    if (!overlay) return;

    function handleWheel(event: WheelEvent) {
      event.preventDefault();

      const unit =
        event.deltaMode === WheelEvent.DOM_DELTA_LINE
          ? 16
          : event.deltaMode === WheelEvent.DOM_DELTA_PAGE
            ? window.innerHeight
            : 1;

      if (event.ctrlKey || event.metaKey) {
        applyZoom(
          scaleRef.current * Math.exp(-event.deltaY * unit * WHEEL_ZOOM_SPEED),
          { x: event.clientX, y: event.clientY },
        );
        return;
      }

      panBy(-event.deltaX * unit, -event.deltaY * unit);
    }

    overlay.addEventListener("wheel", handleWheel, { passive: false });
    return () => overlay.removeEventListener("wheel", handleWheel);
  }, [applyZoom, panBy]);

  useEffect(() => {
    if (images.length < 2) return;

    const previousIndex = (safeIndex - 1 + images.length) % images.length;
    const nextIndex = (safeIndex + 1) % images.length;

    [images[previousIndex], images[nextIndex]].forEach((image) => {
      if (!image) return;
      const preloadedImage = new window.Image();
      preloadedImage.decoding = "async";
      preloadedImage.src = image.src;
    });
  }, [images, safeIndex]);

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

    if (target instanceof Element && target.closest("button, a")) return;

    // Флаг прошлого жеста не должен пережить начало нового — иначе
    // следующий клик по фону «съедался» бы и просмотр не закрывался.
    ignoreNextOverlayClickRef.current = false;

    const point = { x: event.clientX, y: event.clientY };
    pointersRef.current.set(event.pointerId, point);
    event.currentTarget.setPointerCapture?.(event.pointerId);

    if (pointersRef.current.size === 1) {
      pointerStartRef.current = { ...point, time: Date.now() };
      pointerStartedOnImageRef.current = target === imageRef.current;
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
      setIsGesturing(true);
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

      commitView(nextScale, getClampedOffset(nextOffset, nextScale));
      return;
    }

    if (
      pointersRef.current.size === 1 &&
      scaleRef.current > MIN_SCALE &&
      panLastPointRef.current
    ) {
      const deltaX = point.x - panLastPointRef.current.x;
      const deltaY = point.y - panLastPointRef.current.y;
      const start = pointerStartRef.current;

      panLastPointRef.current = point;
      panBy(deltaX, deltaY);

      if (
        start &&
        Math.hypot(point.x - start.x, point.y - start.y) > TAP_MAX_DISTANCE
      ) {
        ignoreNextOverlayClickRef.current = true;
        if (!isGesturing) setIsGesturing(true);
      }
    }
  }

  function handlePointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    const releasedPoint = pointersRef.current.get(event.pointerId);
    const pointerStart = pointerStartRef.current;
    const wasPinching = pinchStartRef.current !== null;

    pointersRef.current.delete(event.pointerId);

    if (pointersRef.current.size === 1) {
      const [remainingPoint] = Array.from(pointersRef.current.values());
      panLastPointRef.current = remainingPoint;
      pointerStartRef.current = { ...remainingPoint, time: Date.now() };
      pinchStartRef.current = null;
      if (wasPinching && scaleRef.current < SNAP_TO_FIT_SCALE) resetZoom();
      return;
    }

    panLastPointRef.current = null;
    pinchStartRef.current = null;
    setIsGesturing(false);

    if (wasPinching && scaleRef.current < SNAP_TO_FIT_SCALE) {
      resetZoom();
    }

    if (!pointerStart || !releasedPoint) {
      pointerStartRef.current = null;
      return;
    }

    pointerStartRef.current = null;

    // Клик по самой картинке не закрывает просмотр, куда бы браузер ни
    // отправил click при захвате указателя (setPointerCapture на оверлее).
    if (pointerStartedOnImageRef.current) {
      ignoreNextOverlayClickRef.current = true;
    }

    const deltaX = releasedPoint.x - pointerStart.x;
    const deltaY = releasedPoint.y - pointerStart.y;
    const absoluteX = Math.abs(deltaX);
    const absoluteY = Math.abs(deltaY);
    const duration = Date.now() - pointerStart.time;
    const movedDistance = Math.hypot(deltaX, deltaY);

    if (movedDistance <= TAP_MAX_DISTANCE && duration <= TAP_MAX_DURATION) {
      const now = Date.now();
      const lastTap = lastTapRef.current;
      const isRepeatTap =
        lastTap !== null &&
        now - lastTap.time <= DOUBLE_TAP_DELAY &&
        Math.hypot(releasedPoint.x - lastTap.x, releasedPoint.y - lastTap.y) <=
          36;

      // Мышь: курсор над картинкой — «лупа», значит один клик и увеличивает
      // (раньше работал только двойной). Второй клик двойного клика
      // пропускаем, чтобы он тут же не отменил первый.
      if (event.pointerType === "mouse") {
        lastTapRef.current = { ...releasedPoint, time: now };
        if (pointerStartedOnImageRef.current && !isRepeatTap) {
          toggleZoom(releasedPoint);
        }
        return;
      }

      // Палец: одиночное касание ничего не делает, двойное — масштаб.
      if (isRepeatTap) {
        toggleZoom(releasedPoint);
        lastTapRef.current = null;
        ignoreNextOverlayClickRef.current = true;
        return;
      }

      lastTapRef.current = { ...releasedPoint, time: now };
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
      close();
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
    setIsGesturing(false);
  }

  function handleOverlayClick(event: MouseEvent<HTMLDivElement>) {
    if (ignoreNextOverlayClickRef.current) {
      ignoreNextOverlayClickRef.current = false;
      return;
    }

    if (event.defaultPrevented) return;
    close();
  }

  if (!activeImage || typeof document === "undefined") return null;

  const isZoomed = scale > MIN_SCALE;

  return createPortal(
    <div
      ref={overlayRef}
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onClick={handleOverlayClick}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerCancel}
    >
      <h2 id={titleId} className={styles.srOnly}>
        Просмотр изображений
      </h2>

      <button
        ref={closeButtonRef}
        className={styles.closeButton}
        type="button"
        aria-label="Закрыть просмотр"
        onClick={(event) => {
          event.stopPropagation();
          close();
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
          key={activeImage.src}
          className={`${styles.image} ${
            isGesturing ? styles.imageGesturing : ""
          }`}
          src={activeImage.src}
          alt={activeImage.alt}
          decoding="async"
          draggable={false}
          style={{
            transform: `translate3d(${offset.x}px, ${offset.y}px, 0) scale(${scale})`,
            cursor: isZoomed ? (isGesturing ? "grabbing" : "grab") : "zoom-in",
          }}
          onClick={(event) => event.stopPropagation()}
        />
      </div>

      {images.length > 1 && !isZoomed && (
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
          aria-label="Уменьшить"
          disabled={!isZoomed}
          onClick={() => applyZoom(scaleRef.current - ZOOM_STEP)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 12h12" />
          </svg>
        </button>
        <button
          className={styles.zoomValue}
          type="button"
          aria-label="Показать изображение целиком"
          disabled={!isZoomed}
          onClick={resetZoom}
        >
          {Math.round(scale * 100)}%
        </button>
        <button
          type="button"
          aria-label="Увеличить"
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
          {safeIndex + 1} / {images.length}
        </span>
      </div>
    </div>,
    document.body,
  );
}
