from django.conf import settings
from django.core.checks import Warning, register


@register()
def lead_phone_encryption_key(app_configs, **kwargs):
    """Без ключа телефоны в заявках сохраняются незашифрованными (leads/crypto.py)."""
    if settings.DEBUG or getattr(settings, "LEAD_PHONE_ENCRYPTION_KEY", ""):
        return []

    return [
        Warning(
            "LEAD_PHONE_ENCRYPTION_KEY не задан — телефоны в заявках "
            "сохраняются незашифрованными.",
            hint=(
                "Задайте длинную случайную строку в backend/.env.prod, "
                "перезапустите backend и выполните "
                "python manage.py encrypt_lead_phones."
            ),
            id="leads.W001",
        )
    ]
