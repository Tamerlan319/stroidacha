import Link from "next/link";

import CookieSettingsButton from "../components/CookieSettingsButton";
import { legalConfig } from "../lib/legalConfig";
import { COOKIE_CONSENT_STORAGE_KEY } from "../lib/cookieConsentKey";
import styles from "../components/LegalPage.module.css";

export default function CookiesPage() {
  return (
    <main className={styles.page}>
      <span className={styles.eyebrow}>Документы</span>
      <h1>Политика использования cookie</h1>
      <div className={styles.meta}>
        Редакция от {legalConfig.consentVersion} · Оператор: {legalConfig.legalName}
      </div>

      <p>
        Cookie и похожие технологии (записи в хранилище браузера) — небольшие
        данные, которые сайт сохраняет в браузере. При первом входе на сайт
        показывается окно выбора. Необходимые cookie работают всегда. Яндекс
        Метрика работает с момента входа и отключается, если нажать «Только
        необходимые». Карты Яндекса загружаются после «Принять все».
      </p>

      <h2>Какие cookie используются</h2>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Вид</th>
              <th>Что и зачем</th>
              <th>Когда работают</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Необходимые</td>
              <td>
                Ваш выбор в баннере cookie (запись{" "}
                <code>{COOKIE_CONSENT_STORAGE_KEY}</code>, хранится, пока вы её
                не удалите); состояние каталога, чтобы кнопка «Назад»
                возвращала к тому же месту (до закрытия вкладки). Сотрудникам в
                административной части — cookie входа и защиты форм.
              </td>
              <td>Всегда: без них сайт не работает как задумано</td>
            </tr>
            <tr>
              <td>Аналитические</td>
              <td>
                Яндекс Метрика (ООО «ЯНДЕКС»): cookie <code>_ym_uid</code>,{" "}
                <code>_ym_d</code> и другие, записи в хранилище браузера.
                Собирает сведения о посещениях: страницы, клики и действия, в
                том числе записи посещений (Вебвизор), устройство, браузер,
                IP-адрес. Ввод в поля формы заявки не записывается. Перечень и
                сроки хранения cookie —{" "}
                <a
                  href="https://yandex.ru/support/metrica/ru/general/cookie-usage"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  в справке Яндекс Метрики
                </a>
                .
              </td>
              <td>
                С момента входа на сайт; не работают после «Только
                необходимые»
              </td>
            </tr>
            <tr>
              <td>Сторонние виджеты</td>
              <td>
                Карты Яндекса на главной и в контактах, отзывы с Яндекс Карт.
                При загрузке Яндекс может установить свои cookie.
              </td>
              <td>
                После «Принять все» или когда вы сами нажимаете «Показать
                карту» / «Показать отзывы»
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>Как изменить выбор</h2>
      <p>
        Выбор можно изменить или отозвать согласие в любой момент — кнопкой ниже
        или ссылкой «Настройки cookie» в подвале сайта. После отказа страница
        перезагрузится, и Метрика больше не будет загружаться. Сохранённые
        cookie можно удалить в настройках браузера.
      </p>
      <p>
        <CookieSettingsButton className={styles.settingsButton} />
      </p>

      <p>
        Как обрабатываются персональные данные — в{" "}
        <Link href="/privacy">политике обработки персональных данных</Link>.
      </p>
    </main>
  );
}
