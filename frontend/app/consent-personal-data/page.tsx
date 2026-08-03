import { legalConfig } from "../lib/legalConfig";
import styles from "../components/LegalPage.module.css";

export default function ConsentPersonalDataPage() {
  return (
    <main className={styles.page}>
      <span className={styles.eyebrow}>Документы</span>
      <h1>Согласие на обработку персональных данных</h1>
      <div className={styles.meta}>
        Версия: {legalConfig.consentVersion}
      </div>

      <p>
        Пользователь, отправляя форму на сайтах {legalConfig.sites.join(" и ")},
        даёт {legalConfig.legalName} согласие на обработку персональных данных.
      </p>

      <h2>Перечень данных</h2>
      <ul>
        <li>номер телефона;</li>
        <li>содержание обращения;</li>
        <li>прикреплённые файлы;</li>
        <li>IP-адрес, user-agent, дата и адрес страницы отправки.</li>
      </ul>

      <h2>Цели обработки</h2>
      <ul>
        <li>рассмотрение обращения;</li>
        <li>связь с пользователем по проекту;</li>
        <li>подготовка консультации и расчёта;</li>
        <li>защита сайта от спама и злоупотреблений.</li>
      </ul>

      <h2>Срок действия согласия</h2>
      <p>
        Согласие действует до достижения целей обработки либо до момента его
        отзыва субъектом персональных данных.
      </p>

      <h2>Порядок отзыва</h2>
      <p>
        Отзыв направляется на адрес {legalConfig.privacyEmail} с указанием номера
        телефона, использованного при обращении.
      </p>
    </main>
  );
}
