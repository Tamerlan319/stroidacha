"use client";

import { FormEvent, useState } from "react";

type LeadFormProps = {
  source?: string;
  projectSlug?: string;
  title?: string;
};

type FormState = {
  name: string;
  phone: string;
  email: string;
  message: string;
};

export default function LeadForm({
  source = "contact_form",
  projectSlug = "",
  title = "Оставить заявку",
}: LeadFormProps) {
  const [form, setForm] = useState<FormState>({
    name: "",
    phone: "",
    email: "",
    message: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function getUtmValue(name: string) {
    if (typeof window === "undefined") {
      return "";
    }

    const params = new URLSearchParams(window.location.search);
    return params.get(name) || "";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setStatus("idle");
    setErrorMessage("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;

      const response = await fetch(`${apiUrl}/leads/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: form.name,
          phone: form.phone,
          email: form.email,
          message: form.message,
          source,
          project_slug: projectSlug,
          page_url: window.location.href,
          utm_source: getUtmValue("utm_source"),
          utm_medium: getUtmValue("utm_medium"),
          utm_campaign: getUtmValue("utm_campaign"),
          utm_content: getUtmValue("utm_content"),
          utm_term: getUtmValue("utm_term"),
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(
          data?.phone?.[0] ||
            data?.project_slug?.[0] ||
            "Не удалось отправить заявку"
        );
      }

      setForm({
        name: "",
        phone: "",
        email: "",
        message: "",
      });

      setStatus("success");
    } catch (error) {
      setStatus("error");
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Произошла ошибка при отправке заявки"
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="leadForm" onSubmit={handleSubmit}>
      <h3>{title}</h3>

      <p>
        Оставьте контакты — менеджер свяжется с вами, уточнит детали проекта и
        поможет с расчётом.
      </p>

      <div className="formGrid">
        <label>
          <span>Имя</span>
          <input
            type="text"
            value={form.name}
            onChange={(event) => updateField("name", event.target.value)}
            placeholder="Ваше имя"
          />
        </label>

        <label>
          <span>Телефон *</span>
          <input
            type="tel"
            value={form.phone}
            onChange={(event) => updateField("phone", event.target.value)}
            placeholder="+7 999 123-45-67"
            required
          />
        </label>

        <label>
          <span>Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(event) => updateField("email", event.target.value)}
            placeholder="client@example.com"
          />
        </label>

        <label className="formFull">
          <span>Комментарий</span>
          <textarea
            value={form.message}
            onChange={(event) => updateField("message", event.target.value)}
            placeholder="Например: интересует дом из бруса 6х6 под усадку"
            rows={4}
          />
        </label>
      </div>

      <button className="buttonPrimary formButton" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Отправляем..." : "Отправить заявку"}
      </button>

      {status === "success" && (
        <div className="formSuccess">
          Заявка отправлена. Мы свяжемся с вами в ближайшее время.
        </div>
      )}

      {status === "error" && (
        <div className="formError">{errorMessage}</div>
      )}
    </form>
  );
}