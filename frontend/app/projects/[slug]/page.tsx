import LeadForm from "../../components/LeadForm";

type ProjectCategory = {
  id: number;
  title: string;
  slug: string;
};

type PriceOption = {
  id: number;
  group_title: string;
  title: string;
  price: number | null;
  note: string;
};

type Addon = {
  id: number;
  group_title: string;
  title: string;
  price: number | null;
  description: string;
};

type PackageItem = {
  id: number;
  title: string;
  value: string;
};

type PackageSection = {
  id: number;
  title: string;
  items: PackageItem[];
};

type ProjectPackage = {
  id: number;
  title: string;
  description: string;
  sections: PackageSection[];
};

type ProjectImage = {
  id: number;
  image: string;
  image_type: string;
  caption: string;
  alt_text: string;
  sort_order: number;
};

type ProjectPlan = {
  id: number;
  title: string;
  image: string;
  floor: number | null;
  alt_text: string;
  sort_order: number;
};

type Project = {
  id: number;
  external_id: string | null;
  title: string;
  slug: string;
  category: ProjectCategory;
  area: string | null;
  floor_label: string;
  size_text: string;
  price_from: number | null;
  short_description: string;
  description: string;
  main_image: string | null;
  price_options: PriceOption[];
  addons: Addon[];
  packages: ProjectPackage[];
  images: ProjectImage[];
  plans: ProjectPlan[];
};

type PageProps = {
  params: Promise<{
    slug: string;
  }>;
};

async function getProject(slug: string): Promise<Project> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/projects/${slug}/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Не удалось загрузить проект");
  }

  return response.json();
}

function formatPrice(price: number | null) {
  if (!price) {
    return "по запросу";
  }

  return `${price.toLocaleString("ru-RU")} ₽`;
}

function groupByTitle<T extends { group_title: string }>(items: T[]) {
  return items.reduce<Record<string, T[]>>((acc, item) => {
    const group = item.group_title || "Прочее";

    if (!acc[group]) {
      acc[group] = [];
    }

    acc[group].push(item);

    return acc;
  }, {});
}

export default async function ProjectPage({ params }: PageProps) {
  const { slug } = await params;
  const project = await getProject(slug);

  const priceGroups = groupByTitle(project.price_options);
  const addonGroups = groupByTitle(project.addons);

  return (
    <main>
      <section className="projectHero">
        <div className="container projectHeroGrid">
          <div>
            <p className="eyebrow">{project.category.title}</p>
            <h1>{project.title}</h1>

            <p className="heroText">
              {project.short_description ||
                "Подробная карточка проекта с характеристиками, ценами и комплектацией."}
            </p>

            <div className="projectMeta">
              {project.area && <span>{project.area} м²</span>}
              {project.size_text && <span>{project.size_text}</span>}
              {project.floor_label && <span>{project.floor_label}</span>}
            </div>

            <div className="heroActions">
              <a href="#prices" className="buttonPrimary">
                Смотреть цены
              </a>
              <a href="tel:+70000000000" className="buttonSecondary">
                Заказать проект
              </a>
            </div>
          </div>

          <div className="projectHeroImage">
            {project.main_image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={project.main_image} alt={project.title} />
            ) : (
              <div className="imagePlaceholder">Фото проекта</div>
            )}
          </div>
        </div>
      </section>
      {project.images?.length > 0 && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Галерея</p>
            <h2>Изображения проекта</h2>
            <p>Внешний вид, детали и дополнительные изображения проекта.</p>
          </div>

          <div className="projectGallery">
            {project.images.map((image) => (
              <figure className="galleryItem" key={image.id}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={image.image}
                  alt={image.alt_text || image.caption || project.title}
                />

                {image.caption && <figcaption>{image.caption}</figcaption>}
              </figure>
            ))}
          </div>
        </section>
      )}
      <section className="container section" id="prices">
        <div className="sectionHeader">
          <p className="eyebrow">Стоимость</p>
          <h2>Цены по материалам</h2>
        </div>

        <div className="priceGroupGrid">
          {Object.entries(priceGroups).map(([groupTitle, items]) => (
            <div className="infoCard" key={groupTitle}>
              <h3>{groupTitle}</h3>

              <div className="priceRows">
                {items.map((item) => (
                  <div className="priceRow" key={item.id}>
                    <span>{item.title}</span>
                    <strong>{formatPrice(item.price)}</strong>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="sectionHeader">
          <p className="eyebrow">Дополнительно</p>
          <h2>Фундамент и кровля</h2>
        </div>

        <div className="priceGroupGrid">
          {Object.entries(addonGroups).map(([groupTitle, items]) => (
            <div className="infoCard" key={groupTitle}>
              <h3>{groupTitle}</h3>

              <div className="priceRows">
                {items.map((item) => (
                  <div className="priceRow" key={item.id}>
                    <span>{item.title}</span>
                    <strong>{formatPrice(item.price)}</strong>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {project.description && (
        <section className="container section">
          <div className="sectionHeader">
            <p className="eyebrow">Описание</p>
            <h2>О проекте</h2>
            <p>{project.description}</p>
          </div>
        </section>
      )}

      <section className="container section">
        <div className="sectionHeader">
          <p className="eyebrow">Комплектация</p>
          <h2>Базовая комплектация</h2>
        </div>

        <div className="packageList">
          {project.packages.map((projectPackage) => (
            <div className="infoCard" key={projectPackage.id}>
              <h3>{projectPackage.title}</h3>

              {projectPackage.sections.map((section) => (
                <div className="packageSection" key={section.id}>
                  <h4>{section.title}</h4>

                  <div className="packageRows">
                    {section.items.map((item) => (
                      <div className="packageRow" key={item.id}>
                        <strong>{item.title}</strong>
                        <span>{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
      <section className="container section">
        <LeadForm
            title="Заказать этот проект"
            source="project_order"
            projectSlug={project.slug}
        />
      </section>
    </main>
  );
}