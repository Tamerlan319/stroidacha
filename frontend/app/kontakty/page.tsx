import type { Metadata } from "next";

import LeadForm from "../components/LeadForm";

export const metadata: Metadata = {
  title: "Контакты | Домодел44",
  description:
    "Контакты компании Домодел44: офис, производство, телефон, email, режим работы и карта проезда.",
};

type ContactLocation = {
  id: number;
  title: string;
  location_type: string;
  location_type_display: string;
  address: string;
  short_description: string;
  phone: string;
  email: string;
  work_hours: string;
  map_embed_url: string;
  map_link_url: string;
  sort_order: number;
};

async function getContacts(): Promise<ContactLocation[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const response = await fetch(`${apiUrl}/contacts/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

function getPrimaryContact(contacts: ContactLocation[]) {
  return (
    contacts.find((contact) => contact.location_type === "office") ||
    contacts[0] ||
    null
  );
}

export default async function ContactsPage() {
  const contacts = await getContacts();
  const primaryContact = getPrimaryContact(contacts);

  return (
    <main className="contactsPage">
      <section className="contactsHero">
        <div className="container contactsHeroInner">
          <div>
            <p className="eyebrow">Контакты</p>

            <h1>Свяжитесь с нами удобным способом</h1>

            <p className="heroText">
              Подскажем по проектам, комплектациям, доставке и строительству.
              Можно приехать в офис по предварительной записи или обсудить
              проект дистанционно.
            </p>
          </div>

          <div className="contactsHeroCard">
            <span>Телефон</span>
            {primaryContact?.phone ? (
              <a href={`tel:${primaryContact.phone}`}>
                {primaryContact.phone}
              </a>
            ) : (
              <strong>Телефон скоро появится</strong>
            )}

            <span>Email</span>
            {primaryContact?.email ? (
              <a href={`mailto:${primaryContact.email}`}>
                {primaryContact.email}
              </a>
            ) : (
              <strong>Email скоро появится</strong>
            )}

            <span>Режим работы</span>
            <strong>{primaryContact?.work_hours || "По предварительной записи"}</strong>
          </div>
        </div>
      </section>

      <section className="container section contactsSection">
        <div className="sectionHeader">
          <p className="eyebrow">Где нас найти</p>
          <h2>Офис, производство и склад</h2>
          <p>
            Контактные точки управляются через Django-админку. Можно добавить
            офис, производство, склад или шоурум.
          </p>
        </div>

        {contacts.length > 0 ? (
          <div className="contactsGrid">
            {contacts.map((contact) => (
              <article className="contactLocationCard" key={contact.id}>
                <div className="contactMap">
                  {contact.map_embed_url ? (
                    <iframe
                      src={contact.map_embed_url}
                      title={contact.title}
                      loading="lazy"
                    />
                  ) : (
                    <div className="contactMapPlaceholder">
                      Карта пока не добавлена
                    </div>
                  )}
                </div>

                <div className="contactLocationBody">
                  <p className="eyebrow">{contact.location_type_display}</p>
                  <h3>{contact.title}</h3>

                  {contact.short_description && (
                    <p className="contactLocationDescription">
                      {contact.short_description}
                    </p>
                  )}

                  <ul className="contactInfoList">
                    <li>
                      <span>Адрес</span>
                      <strong>{contact.address}</strong>
                    </li>

                    {contact.phone && (
                      <li>
                        <span>Телефон</span>
                        <a href={`tel:${contact.phone}`}>{contact.phone}</a>
                      </li>
                    )}

                    {contact.email && (
                      <li>
                        <span>Email</span>
                        <a href={`mailto:${contact.email}`}>{contact.email}</a>
                      </li>
                    )}

                    {contact.work_hours && (
                      <li>
                        <span>Режим работы</span>
                        <strong>{contact.work_hours}</strong>
                      </li>
                    )}
                  </ul>

                  {contact.map_link_url && (
                    <a
                      className="buttonPrimary"
                      href={contact.map_link_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Открыть карту
                    </a>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="catalogState">
            Контактные точки пока не добавлены. Добавьте их в Django admin:
            Content → Контактные точки.
          </div>
        )}
      </section>

      <section className="container section">
        <div className="contactsHelpGrid">
          <article className="infoCard contactsHelpCard">
            <span>01</span>
            <h3>Консультация по проекту</h3>
            <p>
              Поможем подобрать дом, баню или гараж под участок, бюджет и
              нужную комплектацию.
            </p>
          </article>

          <article className="infoCard contactsHelpCard">
            <span>02</span>
            <h3>Расчёт стоимости</h3>
            <p>
              Рассчитаем стоимость с учётом материала, фундамента, кровли,
              доставки и дополнительных опций.
            </p>
          </article>

          <article className="infoCard contactsHelpCard">
            <span>03</span>
            <h3>Доставка по России</h3>
            <p>
              Подготовим домокомплект на производстве и организуем доставку до
              объекта.
            </p>
          </article>
        </div>
      </section>

      <section className="container section" id="lead-form">
        <div className="contactsLeadGrid">
          <div>
            <p className="eyebrow">Заявка</p>
            <h2>Оставьте контакты — мы перезвоним</h2>
            <p>
              Напишите, какой проект вас интересует. Менеджер уточнит детали и
              подскажет ориентировочную стоимость.
            </p>
          </div>

          <LeadForm
            title="Получить консультацию"
            source="contact_form"
            projectSlug=""
          />
        </div>
      </section>
    </main>
  );
}