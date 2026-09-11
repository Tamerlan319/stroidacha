"use client";

import { useState } from "react";

import LightboxViewer, { type LightboxImage } from "./LightboxViewer";

export type { LightboxImage };

type ImageLightboxProps = {
  images: LightboxImage[];
  previewLimit?: number;
  className?: string;
};

// Сетка превью (планировки, портфолио) + полноэкранный просмотр. Сам
// просмотр — общий LightboxViewer, тот же, что в галерее проекта.
export default function ImageLightbox({
  images,
  previewLimit = 5,
  className = "",
}: ImageLightboxProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  if (images.length === 0) return null;

  const previewImages = images.slice(0, previewLimit);
  const hiddenCount = Math.max(images.length - previewImages.length, 0);

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
              onClick={() => setActiveIndex(index)}
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

      {activeIndex !== null && (
        <LightboxViewer
          images={images}
          activeIndex={activeIndex}
          onActiveIndexChange={setActiveIndex}
          onClose={() => setActiveIndex(null)}
        />
      )}
    </>
  );
}
