import { legalConfig } from "../lib/legalConfig";
import styles from "../components/LegalPage.module.css";

export default function CookiesPage() {
  return (
    <main className={styles.page}>
      <span className={styles.eyebrow}>Документы</span>
      <h1>Политика использования cookie</h1>

      <p>
        Сайт использует технические cookie для корректной работы и cookie
        аналитики при наличии согласия пользователя.
      </p>

      <h2>Технические cookie</h2>
      <p>
        Необходимы для сохранения настроек интерфейса, работы форм и безопасной
        отправки обращений.
      </p>

      <h2>Аналитические cookie</h2>
      <p>
        {legalConfig.useYandexMetrica
          ? "На сайте может использоваться Яндекс Метрика для анализа посещаемости и поведения пользователей."
          : "Аналитические cookie используются только при явном подключении аналитики."}
      </p>

      <h2>Как отказаться</h2>
      <p>
        Вы можете отказаться от необязательных cookie через баннер согласия, а
        также изменить настройки браузера.
      </p>
    </main>
  );
}
