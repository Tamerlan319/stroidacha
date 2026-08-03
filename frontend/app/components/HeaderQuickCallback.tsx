"use client";

import { FormEvent, useRef, useState } from "react";

import { legalConfig } from "../lib/legalConfig";
import styles from "./HeaderQuickCallback.module.css";

type Props = {
  source?: string;
  className?: string;
};

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

export default function HeaderQuickCallback({
  source = "callback",
  className = "",
}: Props) {
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const phoneInputRef = useRef<HTMLInputElement>(null);

  function validatePhone(value: string) {
    const digits = getPhoneDigits(value);

    if (!digits) {
      return "Укажите номер телефона.";
    }

    if (digits.length !== 11 || !digits.startsWith("7")) {
      return "Введите номер в формате +7 (999) 123-45-67.";
    }

    return "";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const phoneError = validatePhone(phone);
    if (phoneError) {
      setError(phoneError);
      setStatus("error");
      phoneInputRef.current?.focus();
      return;
    }

    setIsSubmitting(true);
    setError("");
    setStatus("idle");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error("Не настроен адрес API.");
      }

      const body = new FormData();
      body.append("phone", formatPhone(phone));
      body.append("message", "Заявка из мини-формы в шапке сайта.");
      body.append("source", source);
      body.append("consent_accepted", "true");
      body.append("consent_version", legalConfig.consentVersion);

      const response = await fetch(`${apiUrl}/leads/`, {
        method: "POST",
        body,
      });

      if (!response.ok) {
        throw new Error("Не удалось отправить заявку.");
      }

      setPhone("");
      setStatus("success");
    } catch (submitError) {
      setStatus("error");
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Не удалось отправить заявку."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className={`${styles.form} ${className}`.trim()} onSubmit={handleSubmit} noValidate>
      <input
        ref={phoneInputRef}
        className={`${styles.input} ${
          status === "error" && error ? styles.inputInvalid : ""
        }`}
        type="tel"
        inputMode="tel"
        value={phone}
        onChange={(event) => {
          setPhone(formatPhone(event.target.value));
          setError("");
          if (status !== "idle") {
            setStatus("idle");
          }
        }}
        onBlur={() => setError(validatePhone(phone))}
        placeholder="+7 (___) ___-__-__"
        autoComplete="tel"
        maxLength={18}
        aria-invalid={Boolean(error)}
      />
      <button className={styles.button} type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Отправляем..." : "Перезвоните мне"}
      </button>

      {error && <div className={styles.error}>{error}</div>}
      {status === "success" && (
        <div className={styles.success}>
          Заявка отправлена, скоро перезвоним.
        </div>
      )}
    </form>
  );
}
