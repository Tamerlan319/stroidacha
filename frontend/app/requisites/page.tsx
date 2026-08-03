import { legalConfig } from "../lib/legalConfig";
import styles from "../components/LegalPage.module.css";

export default function RequisitesPage() {
  return (
    <main className={styles.page}>
      <span className={styles.eyebrow}>Документы</span>
      <h1>Реквизиты компании</h1>

      <p>
        {legalConfig.brandName} — бренд {legalConfig.legalName}.
      </p>

      <ul>
        <li>{legalConfig.legalName}</li>
        <li>ИНН: {legalConfig.inn}</li>
        <li>ОГРН: {legalConfig.ogrn}</li>
        <li>Юридический адрес: {legalConfig.legalAddress}</li>
        <li>Телефон: {legalConfig.phoneDisplay}</li>
        <li>Email: {legalConfig.email}</li>
        <li>Режим работы: {legalConfig.workHours}</li>
      </ul>
    </main>
  );
}
