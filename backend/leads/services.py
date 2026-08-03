import mimetypes

from django.conf import settings
from django.core.mail import EmailMessage


def notify_managers_about_lead(lead):
    recipients = settings.LEAD_NOTIFICATION_EMAILS

    if not recipients:
        return

    project_title = lead.project.title if lead.project else "Не указан"
    attachments = list(lead.attachments.all())

    subject = f"Новая заявка: {lead.get_source_display()}"

    message = f"""
Новая заявка с сайта
Источник: {lead.get_source_display()}
Телефон: {lead.phone}
Проект: {project_title}
Прикреплено файлов: {len(attachments)}

Комментарий:
{lead.message or "Без комментария"}

Согласие:
Версия: {lead.consent_version or "-"}
Дата: {lead.consent_given_at or "-"}

Страница заявки:
{lead.page_url or "Не указана"}

UTM:
utm_source: {lead.utm_source or "-"}
utm_medium: {lead.utm_medium or "-"}
utm_campaign: {lead.utm_campaign or "-"}
utm_content: {lead.utm_content or "-"}
utm_term: {lead.utm_term or "-"}

Техническая информация:
IP: {lead.ip_address or "-"}
User-Agent: {lead.user_agent or "-"}
""".strip()

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )

    for attachment in attachments:
        try:
            with attachment.file.open("rb") as uploaded_file:
                content = uploaded_file.read()

            content_type = (
                attachment.content_type
                or mimetypes.guess_type(attachment.original_name)[0]
                or "application/octet-stream"
            )
            email.attach(
                attachment.original_name,
                content,
                content_type,
            )
        except (OSError, ValueError):
            continue

    email.send(fail_silently=False)
