"use client";

import { useCallback, useEffect, useState } from "react";

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

export default function ImageLightbox({
  images,
  previewLimit = 5,
  className = "",
}: ImageLightboxProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const activeImage =
    activeIndex !== null && images[activeIndex] ? images[activeIndex] : null;

  const previewImages = images.slice(0, previewLimit);
  const hiddenCount = Math.max(images.length - previewImages.length, 0);

  function openImage(index: number) {
    setActiveIndex(index);
  }

  const closeImage = useCallback(() => {
    setActiveIndex(null);
  }, []);

  const showPrevious = useCallback(() => {
    setActiveIndex((currentIndex) => {
      if (currentIndex === null) {
        return null;
      }

      return (currentIndex - 1 + images.length) % images.length;
    });
  }, [images.length]);

  const showNext = useCallback(() => {
    setActiveIndex((currentIndex) => {
      if (currentIndex === null) {
        return null;
      }

      return (currentIndex + 1) % images.length;
    });
  }, [images.length]);

  useEffect(() => {
    if (activeIndex === null) {
      document.body.style.overflow = "";
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
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
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [activeIndex, closeImage, showNext, showPrevious]);

  if (images.length === 0) {
    return null;
  }

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

      {activeImage && (
        <div
          className="lightboxOverlay"
          role="dialog"
          aria-modal="true"
          onClick={closeImage}
        >
          <div className="lightboxContent">
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
                onClick={(event) => {
                  event.stopPropagation();
                  showPrevious();
                }}
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
              onClick={(event) => event.stopPropagation()}
            />

            {images.length > 1 && (
              <button
                className="lightboxArrow lightboxArrowRight"
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  showNext();
                }}
                aria-label="Следующее изображение"
              >
                ›
              </button>
            )}

            <div
              className="lightboxBottom"
              onClick={(event) => event.stopPropagation()}
            >
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
