import mimetypes

from django.conf import settings
from django.core.mail import EmailMessage


def notify_managers_about_lead(lead):
    """Письмо менеджерам о новой заявке.

    В письме только то, что нужно для ответа клиенту: форма, телефон, проект,
    страница, комментарий и файлы. Технических данных о посетителе в нём нет
    (152-ФЗ, ст. 5 ч. 5): письма живут в почтовом ящике дольше, чем заявка в
    базе.
    """
    recipients = settings.LEAD_NOTIFICATION_EMAILS

    if not recipients:
        return

    project_title = lead.project.title if lead.project else "Не указан"
    attachments = list(lead.attachments.all())

    # Признаки накрутки (leads/fraud.py) — только в этом письме, в базе их нет.
    suspicion_note = getattr(lead, "suspicion_note", "")

    subject = f"Новая заявка: {lead.get_source_display()}"
    if suspicion_note:
        subject += " — проверьте"

    note = (
        f"\nПроверьте заявку: {suspicion_note}.\n"
        "Цель «Заявка отправлена» в Метрику по ней не отправлялась.\n\n"
        if suspicion_note
        else ""
    )

    message = f"""
Новая заявка с сайта
{note}Источник: {lead.get_source_display()}
Телефон: {lead.phone}
Проект: {project_title}
Страница: {lead.page_url or "Не указана"}
Прикреплено файлов: {len(attachments)}

Комментарий:
{lead.message or "Без комментария"}
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
