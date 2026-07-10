"use client";

import { useEffect } from "react";

export default function MobileHorizontalLock() {
  useEffect(() => {
    let startX = 0;
    let startY = 0;

    function isMobile() {
      return window.innerWidth <= 700;
    }

    function isEditable(target: EventTarget | null) {
      if (!(target instanceof HTMLElement)) {
        return false;
      }

      return Boolean(
        target.closest("input, textarea, select, button, a, [contenteditable='true']")
      );
    }

    function handleTouchStart(event: TouchEvent) {
      if (!isMobile() || event.touches.length !== 1) {
        return;
      }

      startX = event.touches[0].clientX;
      startY = event.touches[0].clientY;
    }

    function handleTouchMove(event: TouchEvent) {
      if (!isMobile() || event.touches.length !== 1) {
        return;
      }

      if (isEditable(event.target)) {
        return;
      }

      const currentX = event.touches[0].clientX;
      const currentY = event.touches[0].clientY;

      const diffX = currentX - startX;
      const diffY = currentY - startY;

      const isHorizontalSwipe =
        Math.abs(diffX) > 8 && Math.abs(diffX) > Math.abs(diffY) * 1.15;

      if (isHorizontalSwipe) {
        event.preventDefault();
      }
    }

    window.addEventListener("touchstart", handleTouchStart, {
      passive: true,
    });

    window.addEventListener("touchmove", handleTouchMove, {
      passive: false,
    });

    return () => {
      window.removeEventListener("touchstart", handleTouchStart);
      window.removeEventListener("touchmove", handleTouchMove);
    };
  }, []);

  return null;
}