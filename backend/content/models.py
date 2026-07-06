from django.db import models


class Advantage(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    description = models.TextField("Описание", blank=True)
    icon = models.CharField(
        "Иконка",
        max_length=50,
        blank=True,
        help_text="Например: factory, truck, warranty, price",
    )
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Преимущество"
        verbose_name_plural = "Преимущества"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class WorkStep(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Этап работы"
        verbose_name_plural = "Этапы работы"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField("Вопрос", max_length=500)
    answer = models.TextField("Ответ")
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question


class Review(models.Model):
    author_name = models.CharField("Имя клиента", max_length=255)
    city = models.CharField("Город", max_length=255, blank=True)
    text = models.TextField("Отзыв")
    project_name = models.CharField("Проект/объект", max_length=255, blank=True)
    rating = models.PositiveSmallIntegerField("Оценка", default=5)
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.author_name} — {self.rating}/5"