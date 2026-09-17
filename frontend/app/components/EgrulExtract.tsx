import { EGRUL_CHECK_URL, egrulExtract as data } from "../lib/egrul";
import { optimizedImageUrl } from "../lib/imageUrl";
import styles from "./EgrulExtract.module.css";

type ScanImage = {
  id: number;
  image: string | null;
  alt_text: string;
  caption: string;
  sort_order: number;
};

type EgrulExtractProps = {
  images: ScanImage[];
};

// Номер страницы скана — из имени файла или подписи («…-7.jpg», «страница 7»).
// Порядок в админке уже путался (6 и 7), а у документа он важен.
function pageNumber(image: ScanImage) {
  const match = `${image.image ?? ""} ${image.alt_text}`.match(/(\d+)\D*$/);
  return match ? Number(match[1]) : image.sort_order;
}

// Страница «Выписка из ЕГРЮЛ»: сведения текстом и таблицами, ссылка на
// проверку у ФНС и сканы выписки в свёрнутом блоке.
export default function EgrulExtract({ images }: EgrulExtractProps) {
  const scans = images
    .filter((image) => image.image)
    .sort((a, b) => pageNumber(a) - pageNumber(b));

  const organization: [string, string][] = [
    ["Полное наименование", data.fullName],
    ["Сокращённое наименование", data.shortName],
    ["ИНН", data.inn],
    ["КПП", data.kpp],
    ["ОГРН", data.ogrn],
    ["Дата регистрации", data.registeredAt],
    ["Статус", data.status],
  ];

  return (
    <section className={`container section ${styles.section}`}>
      <div className={styles.verify}>
        <div>
          <p className={styles.eyebrow}>Проверка у ФНС</p>
          <h2>Сведения о компании из ЕГРЮЛ</h2>
          <p className={styles.lead}>
            «Брусодел» — бренд ООО «СтройДача». Всё ниже можно проверить
            самостоятельно в сервисе Федеральной налоговой службы: введите ИНН{" "}
            <b>{data.inn}</b> — сведения откроются сразу, выписку можно скачать
            бесплатно.
          </p>
        </div>
        <a
          className={`buttonPrimary ${styles.verifyButton}`}
          href={EGRUL_CHECK_URL}
          target="_blank"
          rel="noopener noreferrer"
        >
          Проверить на egrul.nalog.ru ↗
        </a>
      </div>

      <div className={styles.grid}>
        <article className={styles.card}>
          <h3>Организация</h3>
          <dl className={styles.rows}>
            {organization.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </article>

        <div className={styles.column}>
          <article className={styles.card}>
            <h3>Адрес и руководство</h3>
            <dl className={styles.rows}>
              <div>
                <dt>Юридический адрес</dt>
                <dd>{data.address}</dd>
              </div>
              <div>
                <dt>{data.directorPosition}</dt>
                <dd>{data.directorName}</dd>
              </div>
              <div>
                <dt>Уставный капитал</dt>
                <dd>{data.charterCapital}</dd>
              </div>
              <div>
                <dt>Регистрирующий орган</dt>
                <dd>{data.registrationAuthority}</dd>
              </div>
            </dl>
          </article>

          <article className={styles.card}>
            <h3>Виды деятельности</h3>
            <p className={styles.activityLabel}>Основной</p>
            <p className={styles.activity}>
              <span>{data.mainActivity.code}</span>
              {data.mainActivity.title}
            </p>
            <p className={styles.activityLabel}>Дополнительные, в том числе</p>
            <ul className={styles.activities}>
              {data.additionalActivities.map((activity) => (
                <li key={activity.code} className={styles.activity}>
                  <span>{activity.code}</span>
                  {activity.title}
                </li>
              ))}
            </ul>
          </article>
        </div>
      </div>

      <p className={styles.source}>
        По выписке из ЕГРЮЛ от {data.extractDate}; сведения сверены с
        egrul.nalog.ru {data.checkedAt}. Полный перечень видов деятельности — в
        выписке.
      </p>

      {scans.length > 0 && (
        <details className={styles.scans}>
          <summary>
            Скан выписки из ЕГРЮЛ
            <span>{scans.length} стр.</span>
          </summary>
          <div className={styles.scanGrid}>
            {scans.map((scan) => (
              <a
                key={scan.id}
                href={scan.image ?? "#"}
                target="_blank"
                rel="noopener noreferrer"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={optimizedImageUrl(scan.image ?? "", 640)}
                  alt={scan.alt_text || `Выписка из ЕГРЮЛ — страница ${pageNumber(scan)}`}
                  loading="lazy"
                  decoding="async"
                />
                <span>Страница {pageNumber(scan)}</span>
              </a>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}
