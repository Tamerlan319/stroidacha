from django.contrib.admin.apps import AdminConfig


class BrusodelAdminConfig(AdminConfig):
    """Подключает BrusodelAdminSite как django.contrib.admin.site — см.
    config/admin_site.py. Стандартный, документированный способ Django
    подменить дефолтный AdminSite без правки admin.register() по всему
    проекту (INSTALLED_APPS ниже ссылается на этот AppConfig вместо
    голого "django.contrib.admin")."""

    default_site = "config.admin_site.BrusodelAdminSite"
