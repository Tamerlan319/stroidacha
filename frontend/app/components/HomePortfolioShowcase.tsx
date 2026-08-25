"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

type PortfolioImage = {
  id: number;
  image: string | null;
  caption: string;
  alt_text: string;
};

type PortfolioProject = {
  id: number;
  title: string;
  location: string;
  area: string;
  size_text: string;
  material: string;
  price: string | number | null;
  short_description: string;
  main_image: string | null;
  images: PortfolioImage[];
};

function formatPrice(price: string | number | null) {
  const value = Number(price);
  return price && !Number.isNaN(value)
    ? `${value.toLocaleString("ru-RU")} ₽`
    : "По запросу";
}

export default function HomePortfolioShowcase() {
  const [project, setProject] = useState<PortfolioProject | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isCancelled = false;

    async function loadProject() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        const response = await fetch(`${apiUrl}/portfolio/`);
        if (!response.ok) throw new Error("portfolio unavailable");

        const projects: PortfolioProject[] = await response.json();
        if (!isCancelled) setProject(projects[0] || null);
      } catch {
        if (!isCancelled) setProject(null);
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }

    loadProject();
    return () => { isCancelled = true; };
  }, []);

  if (isLoading) {
    return (
      <div className="builtProjectLoading" aria-label="Загрузка объекта">
        <span /><span /><span />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="builtProjectEmpty">
        <p>Посмотрите фотографии построенных домов и бань в нашем портфолио.</p>
        <Link className="buttonGhost" href="/portfolio">Открыть портфолио</Link>
      </div>
    );
  }

  const photos = [
    project.main_image,
    ...project.images.map((image) => image.image),
  ].filter((image): image is string => Boolean(image));

  return (
    <div className="builtProjectGrid">
      <article className="builtProjectInfo">
        <p className="builtProjectType">Реализованный объект</p>
        <h3>{project.title}</h3>
        {project.short_description && <p className="builtProjectDescription">{project.short_description}</p>}
        <dl>
          {project.area && <div><dt>Площадь</dt><dd>{project.area}</dd></div>}
          {project.size_text && <div><dt>Размер</dt><dd>{project.size_text}</dd></div>}
          {project.material && <div><dt>Материал</dt><dd>{project.material}</dd></div>}
          <div><dt>Стоимость</dt><dd>{formatPrice(project.price)}</dd></div>
        </dl>
        <Link className="buttonGhost" href="/portfolio">Смотреть портфолио</Link>
      </article>

      {photos.slice(0, 4).map((photo, index) => (
        <div className={`builtPhoto ${index === 0 ? "builtPhotoMain" : ""}`} key={photo}>
          <Image
            src={photo}
            alt={`${project.title}, фотография ${index + 1}`}
            fill
            sizes="(max-width: 780px) 50vw, 25vw"
            style={{ objectFit: "cover" }}
          />
        </div>
      ))}
    </div>
  );
}
