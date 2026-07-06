from django.conf import settings
from django.core.mail import send_mail


def notify_managers_about_lead(lead):
    recipients = settings.LEAD_NOTIFICATION_EMAILS

    if not recipients:
        return

    project_title = lead.project.title if lead.project else "Не указан"

    subject = f"Новая заявка: {lead.get_source_display()}"

    message = f"""
Новая заявка с сайта

Источник: {lead.get_source_display()}
Имя: {lead.name or "Не указано"}
Телефон: {lead.phone}
Email: {lead.email or "Не указан"}
Проект: {project_title}

Комментарий:
{lead.message or "Без комментария"}

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

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=False,
    )