"use client";

import { useState } from "react";
import ImageLightbox, { LightboxImage } from "./ImageLightbox";

export type PortfolioItem = {
  id: number;
  title: string;
  location: string;
  description: string;
  area: string;
  size: string;
  material: string;
  price: string;
  mainImage: string;
  images: LightboxImage[];
};

type PortfolioListProps = {
  items: PortfolioItem[];
};

export default function PortfolioList({ items }: PortfolioListProps) {
  const [openItemIds, setOpenItemIds] = useState<number[]>([]);

  function toggleItem(id: number) {
    setOpenItemIds((current) =>
      current.includes(id)
        ? current.filter((itemId) => itemId !== id)
        : [...current, id]
    );
  }

  return (
    <div className="portfolioList">
      {items.map((item) => {
        const isOpen = openItemIds.includes(item.id);

        return (
          <article className="portfolioObject" key={item.id}>
            <div className="portfolioObjectSummary">
              <div className="portfolioObjectImage">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={item.mainImage} alt={item.title} />
              </div>

              <div className="portfolioObjectContent">
                <p className="portfolioObjectLabel">Реализованный объект</p>

                <h2>{item.title}</h2>

                <p>{item.description}</p>

                <ul className="portfolioObjectSpecs">
                  <li>
                    <span>Локация</span>
                    <strong>{item.location}</strong>
                  </li>
                  <li>
                    <span>Площадь</span>
                    <strong>{item.area}</strong>
                  </li>
                  <li>
                    <span>Размер</span>
                    <strong>{item.size}</strong>
                  </li>
                  <li>
                    <span>Материал</span>
                    <strong>{item.material}</strong>
                  </li>
                  <li>
                    <span>Стоимость</span>
                    <strong>{item.price}</strong>
                  </li>
                </ul>
              </div>
            </div>

            <button
              className="portfolioToggle"
              type="button"
              onClick={() => toggleItem(item.id)}
              aria-expanded={isOpen}
            >
              <span>{isOpen ? "Свернуть фотографии" : "Смотреть фотографии"}</span>
              <strong>{isOpen ? "↑" : "↓"}</strong>
            </button>

            {isOpen && (
              <div className="portfolioObjectGallery">
                <ImageLightbox images={item.images} previewLimit={9} />
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}