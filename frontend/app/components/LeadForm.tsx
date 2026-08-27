"use client";

import Link from "next/link";
import Script from "next/script";
import {
  ChangeEvent,
  DragEvent,
  FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { legalConfig } from "../lib/legalConfig";
import SocialLinks from "./SocialLinks";
import styles from "./LeadForm.module.css";

// Пусто, если ключ не задан на сборке — тогда капча просто не рендерится
// (форма продолжает работать как раньше, см. NEXT_PUBLIC_SMARTCAPTCHA_CLIENT_KEY
// в backend/.env.prod.example). Бэкенд аналогично не требует токен, пока
// не настроен SMARTCAPTCHA_SERVER_KEY — см. leads/captcha.py.
const SMARTCAPTCHA_CLIENT_KEY =
  process.env.NEXT_PUBLIC_SMARTCAPTCHA_CLIENT_KEY || "";

type SmartCaptchaRenderParams = {
  sitekey: string;
  hl?: string;
  callback?: (token: string) => void;
};

declare global {
  interface Window {
    smartCaptcha?: {
      render: (
        container: HTMLElement,
        params: SmartCaptchaRenderParams
      ) => number;
      reset: (widgetId?: number) => void;
      destroy: (widgetId?: number) => void;
    };
  }
}

type LeadFormProps = {
  source?: string;
  projectSlug?: string;
  title?: string;
};

type FormState = {
  phone: string;
  message: string;
  consent: boolean;
  website: string;
};

type FieldName = "phone" | "message" | "attachments" | "consent" | "captcha";
type FieldErrors = Partial<Record<FieldName, string>>;

const EMPTY_FORM: FormState = {
  phone: "",
  message: "",
  consent: false,
  website: "",
};

const MAX_FILES = 5;
const MAX_FILE_SIZE = 8 * 1024 * 1024;
const MAX_TOTAL_SIZE = 20 * 1024 * 1024;
const MAX_MESSAGE_LENGTH = 1500;

const ALLOWED_EXTENSIONS = new Set([
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
  ".heic",
  ".heif",
  ".pdf",
]);

function getExtension(fileName: string) {
  const dotIndex = fileName.lastIndexOf(".");
  return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : "";
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
}

function getPhoneDigits(value: string) {
  let digits = value.replace(/\D/g, "");

  if (!digits) {
    return "";
  }

  if (digits.startsWith("8")) {
    digits = `7${digits.slice(1)}`;
  } else if (digits.startsWith("9")) {
    digits = `7${digits}`;
  } else if (!digits.startsWith("7")) {
    digits = `7${digits}`;
  }

  return digits.slice(0, 11);
}

function formatPhone(value: string) {
  const digits = getPhoneDigits(value);

  if (!digits) {
    return "";
  }

  const number = digits.slice(1);
  let formatted = "+7";

  if (number.length > 0) {
    formatted += ` (${number.slice(0, 3)}`;
  }
  if (number.length >= 3) {
    formatted += ")";
  }
  if (number.length > 3) {
    formatted += ` ${number.slice(3, 6)}`;
  }
  if (number.length > 6) {
    formatted += `-${number.slice(6, 8)}`;
  }
  if (number.length > 8) {
    formatted += `-${number.slice(8, 10)}`;
  }

  return formatted;
}

function validateField(
  field: FieldName,
  form: FormState,
  attachments: File[]
): string {
  if (field === "phone") {
    const digits = getPhoneDigits(form.phone);

    if (!digits) {
      return "Укажите номер телефона.";
    }

    if (digits.length !== 11 || !digits.startsWith("7")) {
      return "Введите российский номер в формате +7 (999) 123-45-67.";
    }
  }

  if (field === "message" && form.message.length > MAX_MESSAGE_LENGTH) {
    return `Комментарий не должен быть длиннее ${MAX_MESSAGE_LENGTH} символов.`;
  }

  if (field === "consent" && !form.consent) {
    return "Подтвердите согласие на обработку персональных данных.";
  }

  if (field === "attachments") {
    if (attachments.length > MAX_FILES) {
      return `Можно прикрепить не более ${MAX_FILES} файлов.`;
    }

    const totalSize = attachments.reduce((sum, file) => sum + file.size, 0);
    if (totalSize > MAX_TOTAL_SIZE) {
      return `Общий размер файлов не должен превышать ${formatFileSize(
        MAX_TOTAL_SIZE
      )}.`;
    }

    for (const file of attachments) {
      if (!ALLOWED_EXTENSIONS.has(getExtension(file.name))) {
        return "Поддерживаются JPG, PNG, WEBP, HEIC, HEIF и PDF.";
      }

      if (file.size > MAX_FILE_SIZE) {
        return `Файл «${file.name}» больше ${formatFileSize(MAX_FILE_SIZE)}.`;
      }
    }
  }

  return "";
}

function parseApiErrors(data: unknown): {
  fields: FieldErrors;
  general: string;
} {
  if (!data || typeof data !== "object") {
    return {
      fields: {},
      general: "Не удалось отправить заявку. Попробуйте ещё раз.",
    };
  }

  const fields: FieldErrors = {};
  let general = "";

  for (const [key, rawValue] of Object.entries(data)) {
    const value = Array.isArray(rawValue) ? rawValue[0] : rawValue;
    const message =
      typeof value === "string" ? value : "Проверьте заполнение поля.";

    if (key === "phone" || key === "message" || key === "attachments") {
      fields[key] = message;
    } else if (key === "smartcaptcha_token") {
      fields.captcha = message;
    } else if (key === "non_field_errors" || key === "detail") {
      general = message;
    }
  }

  return {
    fields,
    general: general || "Проверьте отмеченные поля.",
  };
}

export default function LeadForm({
  source = "home_phone_consultation",
  projectSlug = "",
  title = "Записаться на консультацию и расчёт",
}: LeadFormProps) {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [touched, setTouched] = useState<Partial<Record<FieldName, boolean>>>(
    {}
  );
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [generalError, setGeneralError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [captchaToken, setCaptchaToken] = useState("");
  const [isCaptchaScriptLoaded, setIsCaptchaScriptLoaded] = useState(false);

  const phoneInputRef = useRef<HTMLInputElement>(null);
  const messageInputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const captchaContainerRef = useRef<HTMLDivElement>(null);
  const captchaWidgetIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (
      !SMARTCAPTCHA_CLIENT_KEY ||
      !isCaptchaScriptLoaded ||
      !captchaContainerRef.current ||
      captchaWidgetIdRef.current !== null ||
      !window.smartCaptcha
    ) {
      return;
    }

    captchaWidgetIdRef.current = window.smartCaptcha.render(
      captchaContainerRef.current,
      {
        sitekey: SMARTCAPTCHA_CLIENT_KEY,
        hl: "ru",
        callback: (token) => {
          setCaptchaToken(token);
          setErrors((current) => ({ ...current, captcha: undefined }));
        },
      }
    );
  }, [isCaptchaScriptLoaded]);

  useEffect(() => {
    return () => {
      if (captchaWidgetIdRef.current !== null) {
        window.smartCaptcha?.destroy(captchaWidgetIdRef.current);
        captchaWidgetIdRef.current = null;
      }
    };
  }, []);

  function resetCaptcha() {
    setCaptchaToken("");
    if (captchaWidgetIdRef.current !== null) {
      window.smartCaptcha?.reset(captchaWidgetIdRef.current);
    }
  }

  const messageCharactersLeft = MAX_MESSAGE_LENGTH - form.message.length;
  const selectedFilesSize = useMemo(
    () => attachments.reduce((sum, file) => sum + file.size, 0),
    [attachments]
  );

  function getUtmValue(name: string) {
    if (typeof window === "undefined") {
      return "";
    }

    const params = new URLSearchParams(window.location.search);
    return params.get(name) || "";
  }

  function clearFormStatus() {
    if (status !== "idle") {
      setStatus("idle");
    }
    if (generalError) {
      setGeneralError("");
    }
  }

  function updateField<K extends keyof FormState>(
    field: K,
    value: FormState[K]
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
    clearFormStatus();

    const name = field as FieldName;
    if (touched[name]) {
      const nextForm = { ...form, [field]: value };
      setErrors((current) => ({
        ...current,
        [name]: validateField(name, nextForm, attachments) || undefined,
      }));
    }
  }

  function markTouched(field: FieldName) {
    setTouched((current) => ({
      ...current,
      [field]: true,
    }));

    setErrors((current) => ({
      ...current,
      [field]: validateField(field, form, attachments) || undefined,
    }));
  }

  function addFiles(incomingFiles: File[]) {
    clearFormStatus();

    const uniqueFiles = incomingFiles.filter(
      (incoming) =>
        !attachments.some(
          (current) =>
            current.name === incoming.name &&
            current.size === incoming.size &&
            current.lastModified === incoming.lastModified
        )
    );

    const nextFiles = [...attachments, ...uniqueFiles];
    const attachmentError = validateField("attachments", form, nextFiles);

    setTouched((current) => ({
      ...current,
      attachments: true,
    }));

    if (attachmentError) {
      setErrors((current) => ({
        ...current,
        attachments: attachmentError,
      }));
      return;
    }

    setAttachments(nextFiles);
    setErrors((current) => ({
      ...current,
      attachments: undefined,
    }));
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    addFiles(Array.from(event.target.files || []));
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    addFiles(Array.from(event.dataTransfer.files || []));
  }

  function removeFile(index: number) {
    const nextFiles = attachments.filter(
      (_, currentIndex) => currentIndex !== index
    );
    setAttachments(nextFiles);
    setErrors((current) => ({
      ...current,
      attachments: validateField("attachments", form, nextFiles) || undefined,
    }));
    clearFormStatus();
  }

  function validateForm() {
    const fieldsToValidate: FieldName[] = [
      "phone",
      "message",
      "consent",
      "attachments",
    ];

    const nextErrors: FieldErrors = {};
    for (const field of fieldsToValidate) {
      const message = validateField(field, form, attachments);
      if (message) {
        nextErrors[field] = message;
      }
    }

    setTouched({
      phone: true,
      message: true,
      consent: true,
      attachments: true,
    });
    setErrors(nextErrors);

    return nextErrors;
  }

  function focusFirstInvalidField(nextErrors: FieldErrors) {
    if (nextErrors.phone) {
      phoneInputRef.current?.focus();
      return;
    }

    if (nextErrors.message) {
      messageInputRef.current?.focus();
      return;
    }

    if (nextErrors.attachments) {
      fileInputRef.current?.focus();
      return;
    }

    if (nextErrors.consent) {
      document.getElementById("lead-consent")?.focus();
      return;
    }

    if (nextErrors.captcha) {
      captchaContainerRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validateForm();

    if (SMARTCAPTCHA_CLIENT_KEY && !captchaToken) {
      nextErrors.captcha = "Подтвердите, что вы не робот.";
      setTouched((current) => ({ ...current, captcha: true }));
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      setStatus("error");
      setGeneralError("Проверьте отмеченные поля.");
      window.requestAnimationFrame(() => focusFirstInvalidField(nextErrors));
      return;
    }

    setIsSubmitting(true);
    setStatus("idle");
    setGeneralError("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error("Не настроен адрес API для отправки заявки.");
      }

      const body = new FormData();
      body.append("phone", formatPhone(form.phone));
      body.append("message", form.message.trim());
      body.append("consent_accepted", "true");
      body.append("consent_version", legalConfig.consentVersion);
      body.append("website", form.website);
      body.append("source", source);
      body.append("project_slug", projectSlug);
      body.append("page_url", window.location.href);
      body.append("utm_source", getUtmValue("utm_source"));
      body.append("utm_medium", getUtmValue("utm_medium"));
      body.append("utm_campaign", getUtmValue("utm_campaign"));
      body.append("utm_content", getUtmValue("utm_content"));
      body.append("utm_term", getUtmValue("utm_term"));
      body.append("smartcaptcha_token", captchaToken);

      attachments.forEach((file) => body.append("attachments", file));

      const response = await fetch(`${apiUrl}/leads/`, {
        method: "POST",
        body,
      });

      if (!response.ok) {
        const data: unknown = await response.json().catch(() => null);
        const apiErrors = parseApiErrors(data);

        setErrors((current) => ({
          ...current,
          ...apiErrors.fields,
        }));
        throw new Error(apiErrors.general);
      }

      setForm(EMPTY_FORM);
      setAttachments([]);
      setTouched({});
      setErrors({});
      setStatus("success");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      setStatus("error");
      setGeneralError(
        error instanceof Error
          ? error.message
          : "Произошла ошибка при отправке заявки."
      );
    } finally {
      setIsSubmitting(false);
      // Токен SmartCaptcha одноразовый — после любой попытки отправки (успех
      // или ошибка) нужен новый для следующей.
      resetCaptcha();
    }
  }

  function controlClass(field: FieldName, hasValue: boolean) {
    return [
      styles.control,
      touched[field] && errors[field] ? styles.controlInvalid : "",
      touched[field] && !errors[field] && hasValue ? styles.controlValid : "",
    ]
      .filter(Boolean)
      .join(" ");
  }

  return (
    <form
      className={`leadForm ${styles.form}`}
      onSubmit={handleSubmit}
      noValidate
    >
      <h3>{title}</h3>

      <p>
        Оставьте номер телефона — менеджер свяжется с вами, уточнит детали
        проекта и поможет с расчётом.
      </p>

      <div className="formGrid">
        <label className={`formFull ${styles.field}`}>
          <span>
            Телефон <b aria-hidden="true">*</b>
          </span>
          <input
            ref={phoneInputRef}
            className={controlClass(
              "phone",
              getPhoneDigits(form.phone).length === 11
            )}
            type="tel"
            inputMode="tel"
            value={form.phone}
            onChange={(event) =>
              updateField("phone", formatPhone(event.target.value))
            }
            onBlur={() => markTouched("phone")}
            placeholder="+7 (999) 123-45-67"
            autoComplete="tel"
            maxLength={18}
            aria-invalid={Boolean(touched.phone && errors.phone)}
            aria-describedby={errors.phone ? "lead-phone-error" : undefined}
            required
          />
          {touched.phone && errors.phone && (
            <div className={styles.fieldError} id="lead-phone-error" role="alert">
              {errors.phone}
            </div>
          )}
        </label>

        <label className={`formFull ${styles.field}`}>
          <span>
            Описание <em>необязательно</em>
          </span>
          <textarea
            ref={messageInputRef}
            className={controlClass("message", Boolean(form.message.trim()))}
            value={form.message}
            onChange={(event) => updateField("message", event.target.value)}
            onBlur={() => markTouched("message")}
            placeholder="Например: нужна баня 6×6 по своей планировке, участок в Московской области"
            rows={4}
            maxLength={MAX_MESSAGE_LENGTH}
            aria-invalid={Boolean(touched.message && errors.message)}
            aria-describedby="lead-message-counter"
          />
          <div
            className={`${styles.fieldMeta} ${
              messageCharactersLeft < 100 ? styles.fieldMetaWarning : ""
            }`}
            id="lead-message-counter"
          >
            Осталось {messageCharactersLeft} символов
          </div>
          {touched.message && errors.message && (
            <div className={styles.fieldError} role="alert">
              {errors.message}
            </div>
          )}
        </label>

        <div className={`formFull ${styles.attachmentField}`}>
          <div className={styles.attachmentHeading}>
            <span>Фото или планировка</span>
            <small>Необязательно</small>
          </div>

          <div
            className={`${styles.dropZone} ${
              isDragging ? styles.dropZoneActive : ""
            } ${
              touched.attachments && errors.attachments
                ? styles.dropZoneInvalid
                : ""
            }`}
            onDragEnter={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <div className={styles.attachmentIcon} aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M8.5 12.5 13 8a3 3 0 1 1 4.24 4.24l-6.36 6.36a5 5 0 0 1-7.07-7.07l7.07-7.07"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div className={styles.dropZoneText}>
              <strong>Прикрепите эскиз, фото или планировку</strong>
              <span>Перетащите файлы сюда или выберите их с устройства</span>
            </div>

            <button
              className={styles.attachButton}
              type="button"
              onClick={() => fileInputRef.current?.click()}
            >
              Выбрать файлы
            </button>

            <input
              ref={fileInputRef}
              className={styles.hiddenInput}
              type="file"
              accept=".jpg,.jpeg,.png,.webp,.heic,.heif,.pdf,image/jpeg,image/png,image/webp,image/heic,image/heif,application/pdf"
              multiple
              onChange={handleFileChange}
              aria-label="Прикрепить фото или планировку"
            />
          </div>

          <div className={styles.attachmentHint}>
            До 5 файлов: JPG, PNG, WEBP, HEIC или PDF. До 8 МБ каждый.
            {attachments.length > 0 &&
              ` Выбрано: ${attachments.length}, ${formatFileSize(
                selectedFilesSize
              )}.`}
          </div>
          {touched.attachments && errors.attachments && (
            <div className={styles.fieldError} role="alert">
              {errors.attachments}
            </div>
          )}

          {attachments.length > 0 && (
            <ul className={styles.fileList}>
              {attachments.map((file, index) => (
                <li
                  className={styles.fileItem}
                  key={`${file.name}-${file.size}-${file.lastModified}`}
                >
                  <div className={styles.filePreview} aria-hidden="true">
                    {getExtension(file.name) === ".pdf" ? "PDF" : "IMG"}
                  </div>

                  <div className={styles.fileMeta}>
                    <strong title={file.name}>{file.name}</strong>
                    <span>{formatFileSize(file.size)}</span>
                  </div>

                  <button
                    className={styles.removeFile}
                    type="button"
                    onClick={() => removeFile(index)}
                    aria-label={`Удалить файл ${file.name}`}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className={styles.honeypot} aria-hidden="true">
        <label>
          Ваш сайт
          <input
            type="text"
            name="website"
            value={form.website}
            onChange={(event) => updateField("website", event.target.value)}
            tabIndex={-1}
            autoComplete="off"
          />
        </label>
      </div>

      {SMARTCAPTCHA_CLIENT_KEY && (
        <div className={styles.captchaField}>
          <Script
            src="https://smartcaptcha.yandexcloud.net/captcha.js"
            strategy="afterInteractive"
            onLoad={() => setIsCaptchaScriptLoaded(true)}
          />
          <div ref={captchaContainerRef} />
          {touched.captcha && errors.captcha && (
            <div className={styles.fieldError} role="alert">
              {errors.captcha}
            </div>
          )}
        </div>
      )}

      <label
        className={`${styles.consent} ${
          touched.consent && errors.consent ? styles.consentInvalid : ""
        }`}
      >
        <input
          id="lead-consent"
          type="checkbox"
          checked={form.consent}
          onChange={(event) => {
            updateField("consent", event.target.checked);
            setTouched((current) => ({
              ...current,
              consent: true,
            }));
            setErrors((current) => ({
              ...current,
              consent: event.target.checked
                ? undefined
                : "Подтвердите согласие на обработку персональных данных.",
            }));
          }}
          aria-invalid={Boolean(touched.consent && errors.consent)}
          required
        />
        <span>
          Я даю{" "}
          <Link href="/consent-personal-data">согласие на обработку персональных данных</Link>{" "}
          ООО «СтройДача» для ответа на обращение и ознакомлен с{" "}
          <Link href="/privacy">Политикой обработки персональных данных</Link>
          <b aria-hidden="true">*</b>
        </span>
      </label>

      {touched.consent && errors.consent && (
        <div className={styles.fieldError} role="alert">
          {errors.consent}
        </div>
      )}

      <div className={styles.actionRow}>
        <button
          className={`buttonPrimary formButton ${styles.submitButton}`}
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting && <span className={styles.spinner} aria-hidden="true" />}
          {isSubmitting ? "Отправляем заявку..." : "Отправить заявку"}
        </button>

        <div className={styles.altContact}>
          <span>Или напишите нам напрямую</span>
          <SocialLinks />
        </div>
      </div>

      {status === "success" && (
        <div className={styles.successMessage} aria-live="polite">
          <span aria-hidden="true">✓</span>
          <div>
            <strong>Заявка отправлена</strong>
            <p>Менеджер свяжется с вами в ближайшее рабочее время.</p>
          </div>
        </div>
      )}

      {status === "error" && generalError && (
        <div className={styles.generalError} role="alert" aria-live="assertive">
          {generalError}
        </div>
      )}
    </form>
  );
}
