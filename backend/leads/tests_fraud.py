from datetime import timedelta
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.utils import timezone
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
        ip_address="203.0.113.10",
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
            REMOTE_ADDR=ip_address,
        )

    def test_regular_lead_counts_goal(self):
        response = self.post_lead()

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], True)
        lead = Lead.objects.get()
        self.assertFalse(lead.is_suspicious)
        self.assertEqual(lead.suspicion_reasons, "")

    def test_too_fast_form_is_saved_without_goal(self):
        response = self.post_lead(elapsed="800")

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], False)
        lead = Lead.objects.get()
        self.assertTrue(lead.is_suspicious)
        self.assertIn("быстрее 2 секунд", lead.suspicion_reasons)

    def test_direct_api_call_without_timing_is_suspicious(self):
        response = self.post_lead(elapsed=None)

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], False)

    def test_broken_timing_does_not_reject_lead(self):
        response = self.post_lead(elapsed="abc")

        self.assertEqual(response.status_code, 201)
        self.assertIn("не через форму", Lead.objects.get().suspicion_reasons)

    def test_bot_user_agent_is_suspicious(self):
        response = self.post_lead(user_agent="python-requests/2.31.0")

        self.assertIs(response.data["count_goal"], False)
        self.assertIn("программу", Lead.objects.get().suspicion_reasons)

    def test_repeat_phone_within_day_does_not_count_twice(self):
        first = self.post_lead()
        second = self.post_lead(ip_address="198.51.100.7")

        self.assertIs(first.data["count_goal"], True)
        self.assertIs(second.data["count_goal"], False)
        self.assertEqual(Lead.objects.count(), 2)

    def test_repeat_phone_after_a_day_counts_again(self):
        old = Lead.objects.create(phone=REAL_PHONE)
        Lead.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )

        response = self.post_lead()

        self.assertIs(response.data["count_goal"], True)

    def test_many_phones_from_one_ip(self):
        first = self.post_lead(phone="+7 (916) 482-15-37")
        second = self.post_lead(phone="+7 (926) 731-58-04")
        third = self.post_lead(phone="+7 (903) 264-90-18")

        self.assertIs(first.data["count_goal"], True)
        self.assertIs(second.data["count_goal"], True)
        self.assertIs(third.data["count_goal"], False)

    def test_check_failure_does_not_lose_lead(self):
        with mock.patch(
            "leads.fraud.detect_reasons", side_effect=RuntimeError("boom")
        ):
            with self.assertLogs("leads.fraud", level="ERROR"):
                response = self.post_lead(elapsed=None)

        self.assertEqual(response.status_code, 201)
        self.assertIs(response.data["count_goal"], True)
        self.assertFalse(Lead.objects.get().is_suspicious)

    @override_settings(LEAD_NOTIFICATION_EMAILS=["manager@example.com"])
    def test_manager_email_warns_about_suspicious_lead(self):
        self.post_lead(elapsed="300")

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
