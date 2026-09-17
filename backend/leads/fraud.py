"""Признаки накрученной заявки.

Конкуренты и боты «скручивают» рекламу: заходят с объявления и оставляют
заявку, чтобы Директ засчитал конверсию и учился на мусорном трафике. Такую
заявку не отклоняем — за подозрением может стоять живой клиент: она
сохраняется и уходит менеджерам как обычно, с пометкой «проверьте» в письме.
В ответе API count_goal=false — форма не отправляет по ней цель «Заявка
отправлена» в Метрику (см. frontend/app/components/LeadForm.tsx).

Сама оценка в базе не хранится: всё, что нужно, считается в момент приёма
заявки из данных запроса и уже сохранённых телефонов.
"""

import logging
import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Lead


logger = logging.getLogger(__name__)

# Быстрее живой человек не успеет: открыть форму, ввести номер (или выбрать
# его из автозаполнения), отметить согласие и нажать кнопку. Время форма
# считает с момента своего появления на странице, так что оно всегда не
# меньше настоящего времени заполнения.
MIN_FORM_FILL_MS = 2000
RECENT_WINDOW = timedelta(hours=24)

BOT_USER_AGENT_RE = re.compile(
    r"bots?[/;)]|crawl|spider|headless|phantomjs|selenium|puppeteer|playwright"
    r"|python|curl|wget|httpclient|okhttp|go-http|java/|axios|node-fetch",
    re.IGNORECASE,
)
# Первая цифра кода после +7: в нумерации бывают 3, 4, 8, 9 и 7 (Казахстан),
# номеров на 0, 1, 2, 5 и 6 не существует.
UNUSED_CODE_DIGITS = set("01256")
DIGIT_SEQUENCES = ("0123456789", "9876543210")

REASON_LABELS = {
    "no_form_timing": "отправлена не через форму сайта",
    "too_fast": "форма заполнена быстрее 2 секунд",
    "fake_phone": "номер похож на выдуманный",
    "bot_user_agent": "браузер похож на программу",
    "repeat_phone": "повторная заявка с этого номера за сутки",
}


def looks_like_fake_phone(phone):
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) != 11:
        return False

    number = digits[1:]
    return (
        number[0] in UNUSED_CODE_DIGITS
        or len(set(number)) <= 2
        or any(number[3:] in sequence for sequence in DIGIT_SEQUENCES)
    )


def detect_reasons(*, phone, user_agent, form_elapsed_ms):
    reasons = []

    if form_elapsed_ms is None:
        # Форма сайта всегда присылает время заполнения. Без него заявку
        # отправили в API напрямую, минуя страницу.
        reasons.append("no_form_timing")
    elif form_elapsed_ms < MIN_FORM_FILL_MS:
        reasons.append("too_fast")

    if looks_like_fake_phone(phone):
        reasons.append("fake_phone")

    if not user_agent or BOT_USER_AGENT_RE.search(user_agent):
        reasons.append("bot_user_agent")

    if phone:
        # Телефоны зашифрованы, сравнить их средствами базы нельзя — заявок
        # за сутки единицы, сверяем расшифрованные номера здесь.
        recent_phones = (
            Lead.objects.filter(created_at__gte=timezone.now() - RECENT_WINDOW)
            .exclude(phone="")
            .values_list("phone", flat=True)
        )
        if phone in recent_phones:
            reasons.append("repeat_phone")

    return reasons


def assess_lead(**signals):
    """Причины подозревать заявку одной строкой, пустая строка — чисто.

    Сбой самой проверки не должен стоить заявки: тогда считаем её обычной.
    """
    try:
        # Точка сохранения: ошибка запроса внутри не должна испортить
        # транзакцию, в которой следом создаётся сама заявка.
        with transaction.atomic():
            reasons = detect_reasons(**signals)
    except Exception:
        logger.exception("Не удалось проверить заявку на накрутку")
        return ""

    return "; ".join(REASON_LABELS[reason] for reason in reasons)
