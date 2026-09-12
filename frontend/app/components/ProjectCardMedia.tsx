"use client";

import Image from "next/image";
import Link from "next/link";
import {
  type CSSProperties,
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import styles from "./ProjectCardMedia.module.css";

type ProjectCardMediaProps = {
  href: string;
  title: string;
  badge: string;
  mainImage: string | null;
  planImages?: string[];
  sizes: string;
};

// Сколько держится каждый кадр, пока курсор над карточкой.
const HOVER_SLIDE_INTERVAL_MS = 2000;
// Сдвиг пальца, после которого понятно, листает человек фото или
// прокручивает страницу.
const SWIPE_INTENT_PX = 8;
// Отпустили, протянув кадр на эту долю ширины или быстрым движением, —
// переходим на соседний кадр, иначе возвращаем текущий.
const SWIPE_COMMIT_RATIO = 0.18;
const SWIPE_COMMIT_VELOCITY_PX_PER_MS = 0.35;
const TOUCH_MEDIA_QUERY = "(hover: none), (pointer: coarse)";

type Swipe = {
  pointerId: number;
  startX: number;
  startY: number;
  lastX: number;
  lastTime: number;
  velocity: number;
  axis: "x" | "y" | null;
};

// Фото в карточке каталога. На компьютере при наведении обложка по кругу
// сменяется планировками (обложка → план 1 → план 2 → обложка…), курсор
// ушёл — сразу обратно обложка. На телефоне кадры листаются свайпом.
// Планировки грузятся не сразу: на компьютере — при первом наведении, на
// телефоне — когда карточка подъезжает к экрану. Иначе каталог тянул бы по
// 1–3 лишние картинки на каждую карточку.
export default function ProjectCardMedia({
  href,
  title,
  badge,
  mainImage,
  planImages = [],
  sizes,
}: ProjectCardMediaProps) {
  const slides = [
    ...(mainImage ? [{ src: mainImage, alt: title, isPlan: false }] : []),
    ...planImages.map((src, index) => ({
      src,
      alt: `${title} — планировка ${index + 1}`,
      isPlan: true,
    })),
  ];
  const slideCount = slides.length;

  const [activeIndex, setActiveIndex] = useState(0);
  const [plansRequested, setPlansRequested] = useState(false);

  const activeIndexRef = useRef(0);
  // Первый кадр рендерится сразу, остальные — после запроса, и в показ
  // при наведении попадают только уже загруженные: иначе вместо планировки
  // на пару секунд мелькал бы пустой белый кадр.
  const loadedRef = useRef<boolean[]>([true]);
  const hoveredRef = useRef(false);
  const timerRef = useRef<number | null>(null);
  const linkRef = useRef<HTMLAnchorElement>(null);
  const railRef = useRef<HTMLDivElement>(null);
  const swipeRef = useRef<Swipe | null>(null);
  const suppressClickRef = useRef(false);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
    };
  }, []);

  // Телефон: планировки подгружаем, когда карточка подъезжает к экрану.
  // Раньше они запрашивались первым касанием, и первый свайп по новой
  // карточке не срабатывал — листалось только со второй попытки.
  useEffect(() => {
    if (plansRequested || slideCount < 2) return;

    const link = linkRef.current;
    if (
      !link ||
      !("IntersectionObserver" in window) ||
      !window.matchMedia(TOUCH_MEDIA_QUERY).matches
    ) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setPlansRequested(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px 0px" },
    );
    observer.observe(link);
    return () => observer.disconnect();
  }, [plansRequested, slideCount]);

  function show(index: number) {
    activeIndexRef.current = index;
    setActiveIndex(index);
  }

  function nextReadyIndex(from: number) {
    for (let step = 1; step <= slideCount; step += 1) {
      const candidate = (from + step) % slideCount;
      if (loadedRef.current[candidate]) return candidate;
    }
    return from;
  }

  function stopCycle() {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  function restartCycle() {
    stopCycle();
    timerRef.current = window.setInterval(() => {
      show(nextReadyIndex(activeIndexRef.current));
    }, HOVER_SLIDE_INTERVAL_MS);
  }

  function handleSlideLoaded(index: number) {
    loadedRef.current[index] = true;

    // Планировка догрузилась, пока курсор всё ещё над карточкой, а на экране
    // обложка, — показываем её сразу, не дожидаясь следующего тика.
    if (
      hoveredRef.current &&
      activeIndexRef.current === 0 &&
      nextReadyIndex(0) === index
    ) {
      show(index);
      restartCycle();
    }
  }

  function handlePointerEnter(event: ReactPointerEvent<HTMLAnchorElement>) {
    if (event.pointerType !== "mouse" || slideCount < 2) return;

    hoveredRef.current = true;
    setPlansRequested(true);

    const next = nextReadyIndex(0);
    if (next !== 0) show(next);
    restartCycle();
  }

  function handlePointerLeave(event: ReactPointerEvent<HTMLAnchorElement>) {
    if (event.pointerType !== "mouse") return;

    hoveredRef.current = false;
    stopCycle();
    show(0);
  }

  // Свайп на телефоне считаем сами, а не отдаём прокрутке браузера: у трека
  // touch-action: pan-y (см. CSS), так что браузер забирает себе только
  // вертикальную прокрутку страницы, а горизонтальное движение пальца целиком
  // приходит сюда — в том числе первое касание сразу после прокрутки ленты.
  function setDragOffset(offset: number, dragging: boolean) {
    const rail = railRef.current;
    if (!rail) return;
    rail.style.setProperty("--drag-offset", `${offset}px`);
    rail.dataset.dragging = dragging ? "true" : "false";
  }

  function handlePointerDown(event: ReactPointerEvent<HTMLAnchorElement>) {
    // Второй палец (щипок в предпросмотре карточки) свайп не начинает.
    if (event.pointerType === "mouse" || !event.isPrimary || slideCount < 2) {
      return;
    }

    setPlansRequested(true);
    swipeRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      lastX: event.clientX,
      lastTime: event.timeStamp,
      velocity: 0,
      axis: null,
    };
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLAnchorElement>) {
    const swipe = swipeRef.current;
    if (!swipe || event.pointerId !== swipe.pointerId) return;

    // Долгое нажатие открыло предпросмотр (lib/useCardPeek.ts) — дальше пальцы
    // управляют окном, а не кадрами карточки под ним.
    if (linkRef.current?.closest("[data-peek-open]")) {
      swipeRef.current = null;
      setDragOffset(0, false);
      return;
    }

    const deltaX = event.clientX - swipe.startX;
    const deltaY = event.clientY - swipe.startY;

    if (swipe.axis === null) {
      if (
        Math.abs(deltaX) < SWIPE_INTENT_PX &&
        Math.abs(deltaY) < SWIPE_INTENT_PX
      ) {
        return;
      }
      swipe.axis = Math.abs(deltaX) > Math.abs(deltaY) ? "x" : "y";
      if (swipe.axis === "y") {
        swipeRef.current = null;
        return;
      }
    }

    const elapsed = event.timeStamp - swipe.lastTime;
    if (elapsed > 0) swipe.velocity = (event.clientX - swipe.lastX) / elapsed;
    swipe.lastX = event.clientX;
    swipe.lastTime = event.timeStamp;

    const index = activeIndexRef.current;
    const pullingPastEdge =
      (index === 0 && deltaX > 0) || (index === slideCount - 1 && deltaX < 0);
    setDragOffset(pullingPastEdge ? deltaX / 3 : deltaX, true);
  }

  function finishSwipe(
    event: ReactPointerEvent<HTMLAnchorElement>,
    cancelled: boolean,
  ) {
    const swipe = swipeRef.current;
    if (!swipe || event.pointerId !== swipe.pointerId) return;

    swipeRef.current = null;
    if (swipe.axis !== "x") return;

    // Кадр протащили — отпускание пальца не должно открыть проект.
    suppressClickRef.current = true;
    window.setTimeout(() => {
      suppressClickRef.current = false;
    }, 400);

    let index = activeIndexRef.current;
    if (!cancelled) {
      const width = linkRef.current?.clientWidth || 1;
      const deltaX = event.clientX - swipe.startX;
      const velocity =
        event.timeStamp - swipe.lastTime > 100 ? 0 : swipe.velocity;
      const flick =
        Math.abs(velocity) > SWIPE_COMMIT_VELOCITY_PX_PER_MS
          ? Math.sign(velocity)
          : 0;
      const pulled =
        Math.abs(deltaX) > width * SWIPE_COMMIT_RATIO ? Math.sign(deltaX) : 0;
      // Палец вправо (+1) — предыдущий кадр, влево (−1) — следующий.
      index -= flick || pulled;
    }

    show(Math.min(Math.max(index, 0), slideCount - 1));
    setDragOffset(0, false);
  }

  function handleClickCapture(event: MouseEvent<HTMLAnchorElement>) {
    if (!suppressClickRef.current) return;
    suppressClickRef.current = false;
    event.preventDefault();
    event.stopPropagation();
  }

  return (
    <Link
      ref={linkRef}
      className={`projectImage projectImageSlides ${styles.media}`}
      href={href}
      draggable={false}
      onPointerEnter={handlePointerEnter}
      onPointerLeave={handlePointerLeave}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={(event) => finishSwipe(event, false)}
      onPointerCancel={(event) => finishSwipe(event, true)}
      onClickCapture={handleClickCapture}
    >
      {slideCount === 0 ? (
        <div className="imagePlaceholder">Фото проекта</div>
      ) : (
        <div className={styles.track}>
          <div
            ref={railRef}
            className={styles.rail}
            style={{ "--slide-index": activeIndex } as CSSProperties}
          >
            {slides.map((slide, index) => (
              <div
                key={`${index}-${slide.src}`}
                // Активный кадр читает предпросмотр по долгому нажатию
                // (lib/useCardPeek.ts) — показать ровно то, что на карточке.
                data-card-slide=""
                data-active={index === activeIndex ? "true" : "false"}
                data-src={slide.src}
                data-alt={slide.alt}
                data-plan={slide.isPlan ? "true" : "false"}
                className={[
                  styles.slide,
                  slide.isPlan ? styles.planSlide : "",
                  index === activeIndex ? styles.slideActive : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {(index === 0 || plansRequested) && (
                  <Image
                    src={slide.src}
                    alt={slide.alt}
                    fill
                    sizes={sizes}
                    draggable={false}
                    loading={index === 0 ? undefined : "eager"}
                    style={{ objectFit: slide.isPlan ? "contain" : "cover" }}
                    onLoad={
                      index === 0 ? undefined : () => handleSlideLoaded(index)
                    }
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {slideCount > 1 && (
        <span className={styles.dots} aria-hidden="true">
          {slides.map((slide, index) => (
            <i
              key={`${index}-${slide.src}`}
              className={index === activeIndex ? styles.dotActive : undefined}
            />
          ))}
        </span>
      )}

      <span className="projectBadge">{badge}</span>
    </Link>
  );
}
