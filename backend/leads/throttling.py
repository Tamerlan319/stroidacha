"""Лимиты на приём заявок.

18 сентября 2026 с сайта за 57 минут пришло восемь выдуманных заявок — семь
из всплывающей формы на главной. Прежний лимит (10 в час) их не остановил по
двум причинам: он был слишком мягким и считался в памяти процесса, а
gunicorn запускает двух воркеров — фактический потолок выходил вдвое выше.
Теперь счётчик общий (кэш в базе, см. settings.CACHES), лимитов два: часовой
против залпа и суточный против размазанной по дню накрутки.

Настоящий поток заявок — единицы в день, так что живому человеку эти рамки
не мешают: даже семья, отправившая заявки с одного IP по нескольким
проектам, укладывается.
"""

from rest_framework.throttling import SimpleRateThrottle


class LeadBurstThrottle(SimpleRateThrottle):
    """Заявки с одного адреса за час (LEAD_THROTTLE_RATE)."""

    scope = "leads"

    def get_cache_key(self, request, view):
        # Анонимный эндпоинт: ключ только по адресу. get_ident учитывает
        # X-Forwarded-For от Caddy так же, как serializers.get_client_ip.
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class LeadDailyThrottle(LeadBurstThrottle):
    """Заявки с одного адреса за сутки (LEAD_THROTTLE_RATE_DAY)."""

    scope = "leads_day"
