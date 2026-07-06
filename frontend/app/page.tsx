type ProjectCategory = {
  id: number;
  title: string;
  slug: string;
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
  main_image: string | null;
};

async function getProjects(): Promise<Project[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/projects/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Не удалось загрузить проекты из Django API");
  }

  return response.json();
}

function formatPrice(price: number | null) {
  if (!price) {
    return "Цена по запросу";
  }

  return `от ${price.toLocaleString("ru-RU")} ₽`;
}

export default async function HomePage() {
  const projects = await getProjects();

  return (
    <main>
      <section className="hero">
        <div className="container">
          <p className="eyebrow">Дома, бани и гаражи из бруса</p>

          <h1>Строительство из дерева с собственного производства</h1>

          <p className="heroText">
            Проекты домов, бань и гаражей с понятными комплектациями,
            сроками и ценами. Работаем по региону и организуем строительство
            по России.
          </p>

          <div className="heroActions">
            <a href="#projects" className="buttonPrimary">
              Смотреть проекты
            </a>
            <a href="tel:+70000000000" className="buttonSecondary">
              Позвонить
            </a>
          </div>
        </div>
      </section>

      <section className="container section" id="projects">
        <div className="sectionHeader">
          <p className="eyebrow">Каталог</p>
          <h2>Популярные проекты</h2>
          <p>Эти карточки загружаются из Django API.</p>
        </div>

        <div className="projectGrid">
          {projects.map((project) => (
            <article className="projectCard" key={project.id}>
              <div className="projectImage">
                {project.main_image ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={project.main_image} alt={project.title} />
                ) : (
                  <div className="imagePlaceholder">Фото проекта</div>
                )}
              </div>

              <div className="projectBody">
                <div className="projectTop">
                  <span>{project.category.title}</span>
                  <span>{project.size_text || "Размер уточняется"}</span>
                </div>

                <h3>{project.title}</h3>

                <p>
                  {project.short_description ||
                    "Описание проекта скоро появится."}
                </p>

                <div className="projectSpecs">
                  {project.area && <span>{project.area} м²</span>}
                  {project.floor_label && <span>{project.floor_label}</span>}
                </div>

                <div className="projectFooter">
                  <strong>{formatPrice(project.price_from)}</strong>
                  <a href={`/projects/${project.slug}`}>Подробнее</a>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}