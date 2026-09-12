import {
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

export type CardPeek = {
  src: string;
  alt: string;
  caption: string;
  isPlan: boolean;
  // Уже загруженная картинка карточки — показывается сразу, пока грузится
  // крупная версия для окна.
  placeholderSrc: string;
};

// Сколько держать палец или кнопку мыши, чтобы открылся предпросмотр.
const LONG_PRESS_MS = 400;
// Сдвиг больше этого — человек прокручивает страницу или листает фото,
// а не зажимает карточку.
const MOVE_TOLERANCE_PX = 10;
// Во сколько раз можно увеличить картинку щипком.
const MAX_PINCH_SCALE = 5;
// Слой с картинкой в окне предпросмотра (CardPeekPreview) — его увеличивает
// и двигает щипок. Окно одно, так что находим слой по атрибуту.
const ZOOM_LAYER_SELECTOR = "[data-card-peek-zoom]";

type Point = { x: number; y: number };

type Press = {
  timer: number;
  opened: boolean;
  card: HTMLElement;
};

type Pinch = {
  pointerId: number;
  layer: HTMLElement;
  startDistance: number;
  startScale: number;
  // Точка картинки (в её несдвинутых координатах от центра), которая была
  // под пальцами в начале щипка, — она и остаётся под ними.
  anchor: Point;
};

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

function midpoint(first: Point, second: Point): Point {
  return { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 };
}

// Рамка окна, а не сам слой: у сдвинутого и увеличенного слоя
// getBoundingClientRect уже другой.
function frameOf(layer: HTMLElement) {
  const box = (layer.parentElement ?? layer).getBoundingClientRect();
  return {
    center: { x: box.left + box.width / 2, y: box.top + box.height / 2 },
    width: box.width,
    height: box.height,
  };
}

// Предпросмотр фото карточки каталога по долгому нажатию: окно видно, пока
// палец или кнопка мыши зажаты, отпустили — закрылось. Что показать, берётся
// из активного кадра карточки (data-card-slide в ProjectCardMedia): обложка
// или планировка, до которой человек долистал.
//
// Пока окно открыто, вторым пальцем картинку можно увеличить и подвинуть;
// второй палец отпустили — картинка вернулась к исходному виду, отпустили
// первый — окно закрылось.
export function useCardPeek() {
  const [peek, setPeek] = useState<CardPeek | null>(null);
  const pressRef = useRef<Press | null>(null);
  const pinchRef = useRef<Pinch | null>(null);
  const pointsRef = useRef(new Map<number, Point>());
  const zoomRef = useRef({ scale: 1, x: 0, y: 0 });
  const suppressClickRef = useRef(false);
  const removeListenersRef = useRef<(() => void) | null>(null);

  // Масштаб меняется на каждое движение пальцев — пишем его прямо в стиль
  // слоя, без состояния React: иначе на каждый кадр перерисовывался бы весь
  // каталог.
  const setZoom = useCallback(
    (layer: HTMLElement, scale: number, x: number, y: number, animate: boolean) => {
      zoomRef.current = { scale, x, y };
      layer.style.transition = animate ? "transform 0.22s ease-out" : "none";
      layer.style.transform =
        scale === 1 ? "" : `translate3d(${x}px, ${y}px, 0) scale(${scale})`;
    },
    [],
  );

  const finishPress = useCallback(() => {
    const press = pressRef.current;
    if (press) {
      window.clearTimeout(press.timer);
      delete press.card.dataset.peekOpen;
    }

    removeListenersRef.current?.();
    removeListenersRef.current = null;
    pressRef.current = null;
    pinchRef.current = null;
    pointsRef.current.clear();
    zoomRef.current = { scale: 1, x: 0, y: 0 };

    if (press?.opened) {
      setPeek(null);
      // click, который браузер пришлёт сразу за отпусканием, не должен открыть
      // проект. Если click не пришёл (долгое касание его часто не даёт),
      // сбрасываем флаг, чтобы не съесть следующее настоящее нажатие.
      window.setTimeout(() => {
        suppressClickRef.current = false;
      }, 400);
    }
  }, []);

  useEffect(() => finishPress, [finishPress]);

  function bindCard(caption: string) {
    return {
      onPointerDown(event: ReactPointerEvent<HTMLElement>) {
        if (!event.isPrimary) return;
        if (event.pointerType === "mouse" && event.button !== 0) return;

        finishPress();

        const card = event.currentTarget;
        const { pointerId, pointerType } = event;
        const start = { x: event.clientX, y: event.clientY };
        pointsRef.current.set(pointerId, start);

        const timer = window.setTimeout(() => {
          const slide = card.querySelector<HTMLElement>(
            '[data-card-slide][data-active="true"]',
          );
          const press = pressRef.current;
          if (!slide?.dataset.src || !press) return;

          press.opened = true;
          // Пока окно открыто, палец управляет им, а не кадрами карточки под
          // окном (см. ProjectCardMedia).
          card.dataset.peekOpen = "true";
          suppressClickRef.current = true;
          setPeek({
            src: slide.dataset.src,
            alt: slide.dataset.alt || caption,
            caption,
            isPlan: slide.dataset.plan === "true",
            placeholderSrc: slide.querySelector("img")?.currentSrc || "",
          });

          if (pointerType !== "mouse") navigator.vibrate?.(12);
        }, LONG_PRESS_MS);

        function handlePointerDown(downEvent: PointerEvent) {
          if (downEvent.pointerId === pointerId || downEvent.pointerType === "mouse") {
            return;
          }

          // Второй палец до того, как окно открылось, — это не долгое нажатие.
          if (!pressRef.current?.opened) {
            finishPress();
            return;
          }
          if (pinchRef.current) return;

          const first = pointsRef.current.get(pointerId);
          const layer = document.querySelector<HTMLElement>(ZOOM_LAYER_SELECTOR);
          if (!first || !layer) return;

          const second = { x: downEvent.clientX, y: downEvent.clientY };
          pointsRef.current.set(downEvent.pointerId, second);

          const { center } = frameOf(layer);
          const pinchCenter = midpoint(first, second);
          const { scale, x, y } = zoomRef.current;
          pinchRef.current = {
            pointerId: downEvent.pointerId,
            layer,
            startDistance: Math.max(
              Math.hypot(second.x - first.x, second.y - first.y),
              1,
            ),
            startScale: scale,
            anchor: {
              x: (pinchCenter.x - center.x - x) / scale,
              y: (pinchCenter.y - center.y - y) / scale,
            },
          };
        }

        function handleMove(moveEvent: PointerEvent) {
          const points = pointsRef.current;
          if (!points.has(moveEvent.pointerId)) return;
          points.set(moveEvent.pointerId, {
            x: moveEvent.clientX,
            y: moveEvent.clientY,
          });

          if (!pressRef.current?.opened) {
            const distance = Math.hypot(
              moveEvent.clientX - start.x,
              moveEvent.clientY - start.y,
            );
            if (moveEvent.pointerId === pointerId && distance > MOVE_TOLERANCE_PX) {
              finishPress();
            }
            return;
          }

          const pinch = pinchRef.current;
          const first = points.get(pointerId);
          const second = pinch ? points.get(pinch.pointerId) : undefined;
          if (!pinch || !first || !second) return;

          const { center, width, height } = frameOf(pinch.layer);
          const scale = clamp(
            pinch.startScale *
              (Math.hypot(second.x - first.x, second.y - first.y) /
                pinch.startDistance),
            1,
            MAX_PINCH_SCALE,
          );
          const pinchCenter = midpoint(first, second);
          // Край увеличенной картинки не отходит от края окна.
          const maxX = ((scale - 1) * width) / 2;
          const maxY = ((scale - 1) * height) / 2;

          setZoom(
            pinch.layer,
            scale,
            clamp(pinchCenter.x - center.x - pinch.anchor.x * scale, -maxX, maxX),
            clamp(pinchCenter.y - center.y - pinch.anchor.y * scale, -maxY, maxY),
            false,
          );
        }

        function handleRelease(releaseEvent: PointerEvent) {
          if (releaseEvent.pointerId === pointerId) {
            finishPress();
            return;
          }

          const pinch = pinchRef.current;
          if (pinch?.pointerId === releaseEvent.pointerId) {
            pinchRef.current = null;
            pointsRef.current.delete(releaseEvent.pointerId);
            setZoom(pinch.layer, 1, 0, 0, true);
          }
        }

        // Пока окно открыто, пальцы могут двигаться — страница под окном при
        // этом не прокручивается и не масштабируется (иначе браузер отменит
        // касание и окно закроется само).
        function blockScroll(touchEvent: TouchEvent) {
          if (pressRef.current?.opened && touchEvent.cancelable) {
            touchEvent.preventDefault();
          }
        }

        window.addEventListener("pointerdown", handlePointerDown);
        window.addEventListener("pointermove", handleMove);
        window.addEventListener("pointerup", handleRelease);
        window.addEventListener("pointercancel", handleRelease);
        window.addEventListener("blur", finishPress);
        document.addEventListener("touchmove", blockScroll, { passive: false });

        removeListenersRef.current = () => {
          window.removeEventListener("pointerdown", handlePointerDown);
          window.removeEventListener("pointermove", handleMove);
          window.removeEventListener("pointerup", handleRelease);
          window.removeEventListener("pointercancel", handleRelease);
          window.removeEventListener("blur", finishPress);
          document.removeEventListener("touchmove", blockScroll);
        };

        pressRef.current = { timer, opened: false, card };
      },

      // Долгое касание ссылки на Android открывает системное меню ссылки —
      // пока идёт нажатие, оно не нужно. Правый клик мышью не трогаем.
      onContextMenu(event: MouseEvent<HTMLElement>) {
        if (pressRef.current) event.preventDefault();
      },

      onClickCapture(event: MouseEvent<HTMLElement>) {
        if (!suppressClickRef.current) return;
        suppressClickRef.current = false;
        event.preventDefault();
        event.stopPropagation();
      },
    };
  }

  return { peek, bindCard };
}
