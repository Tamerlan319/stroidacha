"""Кастомный AdminSite — только для того, чтобы добавить сводку и быстрые
ссылки на главную страницу админки (admin/index.html, см. шаблон в
templates/admin/index.html). Права доступа, регистрацию моделей и всё
остальное поведение Django admin не трогает."""

from datetime import timedelta

from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils import timezone


class BrusodelAdminSite(AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["dashboard_stats"] = self._dashboard_stats()
        return super().index(request, extra_context)

    def _dashboard_stats(self):
        # Импорты внутри метода — на момент импорта config/admin_site.py при
        # старте Django приложения ещё не гарантированно готовы (apps not
        # loaded yet), а AdminSite.index() вызывается уже после старта.
        from catalog.models import Project
        from content.models import PortfolioProject, Review
        from leads.models import Lead

        week_ago = timezone.now() - timedelta(days=7)

        # reverse(), не строковый литерал "/admin/..." — иначе ссылки ломаются
        # при любой смене ADMIN_URL_PATH (см. settings.py), что и произошло.
        leads_url = reverse("admin:leads_lead_changelist")
        project_url = reverse("admin:catalog_project_changelist")

        return [
            {
                "label": "Необработанные заявки",
                "value": Lead.objects.filter(is_processed=False).count(),
                "url": f"{leads_url}?is_processed__exact=0",
                "icon": "fas fa-inbox",
                "tone": "warning",
            },
            {
                "label": "Заявки за 7 дней",
                "value": Lead.objects.filter(created_at__gte=week_ago).count(),
                "url": leads_url,
                "icon": "fas fa-chart-line",
                "tone": "info",
            },
            {
                "label": "Активные проекты",
                "value": Project.objects.filter(is_active=True).count(),
                "url": f"{project_url}?is_active__exact=1",
                "icon": "fas fa-home",
                "tone": "success",
            },
            {
                "label": "Объекты портфолио",
                "value": PortfolioProject.objects.filter(is_active=True).count(),
                "url": reverse("admin:content_portfolioproject_changelist"),
                "icon": "fas fa-camera-retro",
                "tone": "success",
            },
            {
                "label": "Отзывы",
                "value": Review.objects.filter(is_active=True).count(),
                "url": reverse("admin:content_review_changelist"),
                "icon": "fas fa-star",
                "tone": "success",
            },
        ]
