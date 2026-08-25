from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateLeadAttachmentStorage(FileSystemStorage):
    """Хранилище для вложений заявок, которое не раздаётся веб-сервером.

    В отличие от MEDIA_ROOT (который Caddy отдаёт как обычную статику
    через /media/*), PRIVATE_MEDIA_ROOT не примонтирован в контейнер Caddy
    вообще — файлы физически недоступны снаружи и отдаются только через
    LeadAttachmentDownloadView с проверкой прав (см. leads/views.py).
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("location", settings.PRIVATE_MEDIA_ROOT)
        super().__init__(**kwargs)

    def url(self, name):
        # Осторожно: FileSystemStorage трактует base_url=None как "взять
        # MEDIA_URL по умолчанию", а не как "URL отключён" — поэтому вместо
        # base_url=None здесь явный raise. Любой код, который случайно
        # попробует получить .url() приватного файла, должен упасть сразу,
        # а не тихо получить путь под /media/, которого для этого файла
        # не существует.
        raise NotImplementedError(
            "PrivateLeadAttachmentStorage не отдаёт публичные URL — "
            "используйте LeadAttachmentDownloadView."
        )
