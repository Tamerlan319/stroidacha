import Link from "next/link";

import styles from "./not-found.module.css";

export default function NotFound() {
  return (
    <main className={styles.page}>
      <div className={styles.glow} aria-hidden="true" />

      <section className={styles.card}>
        <div className={styles.visual} aria-hidden="true">
          <span className={styles.code}>404</span>

          <svg className={styles.house} viewBox="0 0 520 360" fill="none">
            <path
              className={styles.sun}
              d="M409 65a42 42 0 1 0 0 84 42 42 0 0 0 0-84Z"
            />
            <path
              className={styles.land}
              d="M34 300c74-57 141-49 207-8 54 33 107 30 164-7 26-17 53-24 81-17"
            />
            <path
              className={styles.tree}
              d="M82 282v-87m-31 37 31-64 31 64H51Zm9-47 26 53H65l26-53Z"
            />
            <path
              className={styles.tree}
              d="M449 278v-69m-26 31 26-52 26 52h-52Zm8-37 19 38h-38l19-38Z"
            />
            <path
              className={styles.roof}
              d="m155 184 105-88 105 88"
            />
            <path
              className={styles.building}
              d="M178 165v124h164V165L260 98l-82 67Z"
            />
            <path
              className={styles.detail}
              d="M215 289v-72h54v72m23-74h29v34h-29zM197 186h126"
            />
            <path
              className={styles.detail}
              d="M251 240h9m32-8h29M139 289h242"
            />
          </svg>
        </div>

        <div className={styles.content}>
          <p className={styles.eyebrow}>Страница не найдена</p>
          <h1>Похоже, такой страницы больше нет</h1>
          <p className={styles.description}>
            Возможно, адрес изменился или в ссылке допущена ошибка. Вернитесь
            на главную страницу либо перейдите к проектам домов и бань.
          </p>

          <div className={styles.actions}>
            <Link className={styles.primaryButton} href="/">
              На главную
            </Link>
            <Link className={styles.secondaryButton} href="/projects">
              Смотреть проекты
            </Link>
          </div>

          <div className={styles.help}>
            <span>Нужна помощь с выбором проекта?</span>
            <a href="tel:+79676801812">+7 967 680-18-12</a>
          </div>
        </div>
      </section>
    </main>
  );
}
