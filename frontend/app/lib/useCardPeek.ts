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

type Press = {
  timer: number;
  opened: boolean;
};

// Предпросмотр фото карточки каталога по долгому нажатию: окно видно, пока
// палец или кнопка мыши зажаты, отпустили — закрылось. Что показать, берётся
// из активного кадра карточки (data-card-slide в ProjectCardMedia): обложка
// или планировка, до которой человек долистал.
export function useCardPeek() {
  const [peek, setPeek] = useState<CardPeek | null>(null);
  const pressRef = useRef<Press | null>(null);
  const suppressClickRef = useRef(false);
  const removeListenersRef = useRef<(() => void) | null>(null);

  const finishPress = useCallback(() => {
    const press = pressRef.current;
    if (press) window.clearTimeout(press.timer);

    removeListenersRef.current?.();
    removeListenersRef.current = null;
    pressRef.current = null;

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
        const startX = event.clientX;
        const startY = event.clientY;

        const timer = window.setTimeout(() => {
          const slide = card.querySelector<HTMLElement>(
            '[data-card-slide][data-active="true"]',
          );
          const press = pressRef.current;
          if (!slide?.dataset.src || !press) return;

          press.opened = true;
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

        function handleMove(moveEvent: PointerEvent) {
          if (moveEvent.pointerId !== pointerId || pressRef.current?.opened) {
            return;
          }
          const distance = Math.hypot(
            moveEvent.clientX - startX,
            moveEvent.clientY - startY,
          );
          if (distance > MOVE_TOLERANCE_PX) finishPress();
        }

        function handleRelease(releaseEvent: PointerEvent) {
          if (releaseEvent.pointerId === pointerId) finishPress();
        }

        // Пока окно открыто, палец может сдвинуться — страница под окном при
        // этом прокручиваться не должна (иначе браузер отменит касание и
        // окно закроется само).
        function blockScroll(touchEvent: TouchEvent) {
          if (pressRef.current?.opened && touchEvent.cancelable) {
            touchEvent.preventDefault();
          }
        }

        window.addEventListener("pointermove", handleMove);
        window.addEventListener("pointerup", handleRelease);
        window.addEventListener("pointercancel", handleRelease);
        window.addEventListener("blur", finishPress);
        document.addEventListener("touchmove", blockScroll, { passive: false });

        removeListenersRef.current = () => {
          window.removeEventListener("pointermove", handleMove);
          window.removeEventListener("pointerup", handleRelease);
          window.removeEventListener("pointercancel", handleRelease);
          window.removeEventListener("blur", finishPress);
          document.removeEventListener("touchmove", blockScroll);
        };

        pressRef.current = { timer, opened: false };
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
