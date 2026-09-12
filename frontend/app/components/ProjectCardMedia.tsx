"use client";

import Image from "next/image";
import Link from "next/link";
import {
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

// Фото в карточке каталога. На компьютере при наведении обложка по кругу
// сменяется планировками (обложка → план 1 → план 2 → обложка…), курсор
// ушёл — сразу обратно обложка. На телефоне наведения нет, кадры листаются
// свайпом. Планировки грузятся только после первого наведения или касания:
// иначе каталог тянул бы по 1–3 лишние картинки на каждую карточку.
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
  const trackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
    };
  }, []);

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

  function handlePointerDown(event: ReactPointerEvent<HTMLAnchorElement>) {
    if (event.pointerType !== "mouse" && slideCount > 1) {
      setPlansRequested(true);
    }
  }

  function handleScroll() {
    const track = trackRef.current;
    if (!track || track.clientWidth === 0) return;

    const index = Math.round(track.scrollLeft / track.clientWidth);
    if (index !== activeIndexRef.current) show(index);
  }

  return (
    <Link
      className={`projectImage projectImageSlides ${styles.media}`}
      href={href}
      draggable={false}
      onPointerEnter={handlePointerEnter}
      onPointerLeave={handlePointerLeave}
      onPointerDown={handlePointerDown}
    >
      {slideCount === 0 ? (
        <div className="imagePlaceholder">Фото проекта</div>
      ) : (
        <div ref={trackRef} className={styles.track} onScroll={handleScroll}>
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
