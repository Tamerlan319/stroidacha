from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from .fraud import looks_like_fake_phone
from .models import Lead


BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.6.0.0 Safari/537.36"
)
REAL_PHONE = "+7 (916) 482-15-37"


@override_settings(LEAD_NOTIFICATION_EMAILS=[])
class LeadSuspicionTests(APITestCase):
    def post_lead(
        self,
        phone=REAL_PHONE,
        elapsed="9000",
        user_agent=BROWSER_USER_AGENT,
    ):
        # Лимит заявок с одного IP живёт в кэше — здесь проверяем не его.
        cache.clear()
        payload = {
            "phone": phone,
            "source": "contact_form",
            "page_url": "https://brusodel.ru/bani-iz-brusa",
            "consent_accepted": "true",
        }
        if elapsed is not None:
            payload["form_elapsed_ms"] = elapsed

        return self.client.post(
            "/api/leads/",
            payload,
            format="multipart",
            HTTP_USER_AGENT=user_agent,
        )

    def test_regular_lead_counts_goal(self):
        response = self.post_lead()

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], True)

    def test_too_fast_form_is_saved_without_goal(self):
        response = self.post_lead(elapsed="1500")

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], False)
        self.assertEqual(Lead.objects.count(), 1)

    def test_instant_submission_is_rejected(self):
        # Быстрее секунды форму заполняет только скрипт: такую отправку не
        # сохраняем вовсе, чтобы не тревожить менеджеров и владельцев чужих
        # номеров.
        response = self.post_lead(elapsed="200")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)

    def test_direct_api_call_without_timing_is_suspicious(self):
        response = self.post_lead(elapsed=None)

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], False)

    def test_broken_timing_does_not_reject_lead(self):
        response = self.post_lead(elapsed="abc")

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], False)

    def test_bot_user_agent_is_suspicious(self):
        response = self.post_lead(user_agent="python-requests/2.31.0")

        self.assertIs(response.data["count_goal"], False)

    def test_repeat_phone_within_day_does_not_count_twice(self):
        first = self.post_lead()
        second = self.post_lead()

        self.assertIs(first.data["count_goal"], True)
        self.assertIs(second.data["count_goal"], False)
        self.assertEqual(Lead.objects.count(), 2)

    @override_settings(LEAD_PHONE_ENCRYPTION_KEY="test-only-key")
    def test_repeat_phone_is_found_among_encrypted_phones(self):
        first = self.post_lead()
        second = self.post_lead()

        self.assertIs(first.data["count_goal"], True)
        self.assertIs(second.data["count_goal"], False)

    def test_other_phone_same_day_counts(self):
        self.post_lead(phone="+7 (916) 482-15-37")
        response = self.post_lead(phone="+7 (926) 731-58-04")

        self.assertIs(response.data["count_goal"], True)

    def test_check_failure_does_not_lose_lead(self):
        with mock.patch(
            "leads.fraud.detect_reasons", side_effect=RuntimeError("boom")
        ):
            with self.assertLogs("leads.fraud", level="ERROR"):
                response = self.post_lead(elapsed=None)

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], True)

    @override_settings(LEAD_NOTIFICATION_EMAILS=["manager@example.com"])
    def test_manager_email_warns_about_suspicious_lead(self):
        self.post_lead(elapsed="1500")

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].subject.endswith("— проверьте"))
        self.assertIn("быстрее 2 секунд", mail.outbox[0].body)

    @override_settings(LEAD_NOTIFICATION_EMAILS=["manager@example.com"])
    def test_manager_email_for_regular_lead_is_unchanged(self):
        self.post_lead()

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("проверьте", mail.outbox[0].subject)
        self.assertNotIn("Проверьте заявку", mail.outbox[0].body)


class FakePhoneTests(SimpleTestCase):
    def test_real_numbers_pass(self):
        for phone in (REAL_PHONE, "+7 (495) 318-74-02", "+7 (701) 482-15-37"):
            with self.subTest(phone=phone):
                self.assertFalse(looks_like_fake_phone(phone))

    def test_made_up_numbers_are_caught(self):
        for phone in (
            "+7 (999) 999-99-99",
            "+7 (900) 000-00-00",
            "+7 (916) 123-45-67",
            "+7 (555) 482-15-37",
        ):
            with self.subTest(phone=phone):
                self.assertTrue(looks_like_fake_phone(phone))


@override_settings(LEAD_NOTIFICATION_EMAILS=[])
class LeadThrottleTests(APITestCase):
    """Лимиты на приём заявок с одного адреса (leads/throttling.py).

    18.09.2026 с одного IP за 57 минут пришло восемь выдуманных заявок:
    прежний лимит был мягче, а счётчик жил в памяти воркера, так что
    фактический потолок удваивался.
    """

    def setUp(self):
        cache.clear()

    def post_lead(self, phone):
        return self.client.post(
            "/api/leads/",
            {
                "phone": phone,
                "source": "home_hero_popup",
                "page_url": "https://brusodel.ru/",
                "consent_accepted": "true",
                "form_elapsed_ms": "9000",
            },
            format="multipart",
            HTTP_USER_AGENT=BROWSER_USER_AGENT,
        )

    def test_burst_from_one_address_is_cut_off(self):
        codes = [self.post_lead(f"+7 (916) 482-15-{n:02d}") for n in range(40, 47)]
        statuses = [response.status_code for response in codes]

        self.assertEqual(statuses.count(201), 5)
        self.assertEqual(statuses[-1], 429)
        self.assertEqual(Lead.objects.count(), 5)

    def test_limit_is_shared_between_workers(self):
        # Кэш в базе (settings.CACHES) — счётчик общий для всех процессов,
        # а не свой у каждого воркера gunicorn.
        from django.conf import settings

        self.assertEqual(
            settings.CACHES["default"]["BACKEND"],
            "django.core.cache.backends.db.DatabaseCache",
        )
