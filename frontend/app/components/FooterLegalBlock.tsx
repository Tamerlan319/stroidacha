import Link from "next/link";

import { legalConfig } from "../lib/legalConfig";
import styles from "./FooterLegalBlock.module.css";

export default function FooterLegalBlock() {
  return (
    <section className={styles.block}>
      <div className={styles.brand}>
        <strong>{legalConfig.brandName}</strong>
        <span>бренд {legalConfig.legalName}</span>
      </div>

      <div className={styles.grid}>
        <div>
          <div className={styles.label}>Юридическая информация</div>
          <div>{legalConfig.legalName}</div>
          <div>ИНН: {legalConfig.inn}</div>
          <div>ОГРН: {legalConfig.ogrn}</div>
          <div>{legalConfig.legalAddress}</div>
          <div>{legalConfig.workHours}</div>
        </div>

        <div>
          <div className={styles.label}>Контакты</div>
          <div>{legalConfig.phoneDisplay}</div>
          <div>{legalConfig.email}</div>
          <div>{legalConfig.privacyEmail}</div>
        </div>

        <div>
          <div className={styles.label}>Документы</div>
          <Link href="/privacy">Политика обработки персональных данных</Link>
          <Link href="/consent-personal-data">
            Согласие на обработку персональных данных
          </Link>
          <Link href="/cookies">Политика cookie</Link>
          <Link href="/requisites">Реквизиты компании</Link>
        </div>
      </div>
    </section>
  );
}
