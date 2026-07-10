"use client";

import { useEffect, useState } from "react";

export type LightboxImage = {
  id: string | number;
  src: string;
  alt: string;
  caption?: string;
};

type ImageLightboxProps = {
  images: LightboxImage[];
};

export default function ImageLightbox({ images }: ImageLightboxProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const activeImage =
    activeIndex !== null && images[activeIndex] ? images[activeIndex] : null;

  function openImage(index: number) {
    setActiveIndex(index);
  }

  function closeImage() {
    setActiveIndex(null);
  }

    function showPrevious() {
    setActiveIndex((currentIndex) => {
        if (currentIndex === null) {
        return null;
        }

        return (currentIndex - 1 + images.length) % images.length;
    });
    }

    function showNext() {
    setActiveIndex((currentIndex) => {
        if (currentIndex === null) {
        return null;
        }

        return (currentIndex + 1) % images.length;
    });
    }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (activeIndex === null) {
        return;
      }

      if (event.key === "Escape") {
        closeImage();
      }

      if (event.key === "ArrowLeft") {
        showPrevious();
      }

      if (event.key === "ArrowRight") {
        showNext();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    if (activeIndex !== null) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [activeIndex]);

  if (images.length === 0) {
    return null;
  }

  return (
    <>
      <div className="projectGallery">
        {images.map((image, index) => (
          <button
            className={`galleryItem ${index === 0 ? "galleryItemLarge" : ""}`}
            key={image.id}
            type="button"
            onClick={() => openImage(index)}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={image.src} alt={image.alt} />

            {image.caption && <span>{image.caption}</span>}
          </button>
        ))}
      </div>

      {activeImage && (
        <div
          className="lightboxOverlay"
          role="dialog"
          aria-modal="true"
          onClick={closeImage}
        >
          <div
            className="lightboxContent"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              className="lightboxClose"
              type="button"
              onClick={closeImage}
              aria-label="Закрыть"
            >
              ×
            </button>

            {images.length > 1 && (
              <button
                className="lightboxArrow lightboxArrowLeft"
                type="button"
                onClick={showPrevious}
                aria-label="Предыдущее изображение"
              >
                ‹
              </button>
            )}

            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="lightboxImage"
              src={activeImage.src}
              alt={activeImage.alt}
            />

            {images.length > 1 && (
              <button
                className="lightboxArrow lightboxArrowRight"
                type="button"
                onClick={showNext}
                aria-label="Следующее изображение"
              >
                ›
              </button>
            )}

            <div className="lightboxBottom">
              <div>
                {activeImage.caption && <strong>{activeImage.caption}</strong>}
                <span>
                  {(activeIndex ?? 0) + 1} / {images.length}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}