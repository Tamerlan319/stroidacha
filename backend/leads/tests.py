import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Lead, LeadAttachment


class LeadApiComplianceTests(APITestCase):
    def setUp(self):
        # История лимита заявок (ScopedRateThrottle, по IP) живёт в кэше
        # процесса — без очистки тесты, которые шлют заявки, начинают
        # получать 429 в зависимости от порядка запуска.
        cache.clear()
        self.media_directory = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name,
            LEAD_NOTIFICATION_EMAILS=[],
            LEAD_CONSENT_VERSION="2026-08-03",
        )
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def valid_payload(self):
        return {
            "phone": "8 999 123-45-67",
            "message": "Нужна баня 6х6 по своей планировке",
            "source": "home_phone_consultation",
            "project_slug": "",
            "page_url": "https://brusodel.ru/",
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "website": "",
            "consent_accepted": "true",
            "consent_version": "2026-08-03",
        }

    def test_normalizes_phone_and_stores_consent(self):
        response = self.client.post(
            "/api/leads/",
            self.valid_payload(),
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.get()
        self.assertEqual(lead.phone, "+7 (999) 123-45-67")
        self.assertEqual(lead.consent_version, "2026-08-03")
        self.assertIsNotNone(lead.consent_given_at)

    def test_rejects_missing_consent(self):
        payload = self.valid_payload()
        payload["consent_accepted"] = "false"

        response = self.client.post(
            "/api/leads/",
            payload,
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("consent_accepted", response.data)
        self.assertEqual(Lead.objects.count(), 0)

    def test_honeypot_rejects_spam(self):
        payload = self.valid_payload()
        payload["website"] = "https://spam.example"

        response = self.client.post(
            "/api/leads/",
            payload,
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)

    def test_create_lead_with_attachment(self):
        payload = self.valid_payload()
        payload["attachments"] = [
            SimpleUploadedFile(
                "plan.jpg",
                b"test image content",
                content_type="image/jpeg",
            )
        ]

        response = self.client.post(
            "/api/leads/",
            payload,
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(LeadAttachment.objects.count(), 1)

    def test_long_ad_landing_url_does_not_reject_lead(self):
        # Реальный случай: заход из поиска Яндекса с etext в адресе — 201
        # символ, заявка отклонялась по невидимому в форме полю page_url.
        payload = self.valid_payload()
        payload["page_url"] = (
            "https://brusodel.ru/bani-iz-brusa?etext=" + "x" * 153 + "&ybaip=1"
        )

        response = self.client.post("/api/leads/", payload, format="multipart")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.get().page_url, payload["page_url"])

    def test_oversized_metadata_is_truncated_not_rejected(self):
        payload = self.valid_payload()
        payload["page_url"] = "https://brusodel.ru/?q=" + "x" * 3000
        payload["utm_term"] = "дом из бруса " * 30

        response = self.client.post("/api/leads/", payload, format="multipart")

        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.get()
        self.assertEqual(len(lead.page_url), 2000)
        self.assertEqual(len(lead.utm_term), 255)

    def test_non_http_page_url_is_dropped_not_rejected(self):
        payload = self.valid_payload()
        payload["page_url"] = "javascript:alert(1)"

        response = self.client.post("/api/leads/", payload, format="multipart")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.get().page_url, "")

    def test_unknown_source_and_missing_project_do_not_reject_lead(self):
        payload = self.valid_payload()
        payload["source"] = "some_future_form"
        payload["project_slug"] = "project-that-was-removed"

        response = self.client.post("/api/leads/", payload, format="multipart")

        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.get()
        self.assertEqual(lead.source, Lead.Source.CONTACT_FORM)
        self.assertIsNone(lead.project)

    def test_reject_unsupported_attachment(self):
        payload = self.valid_payload()
        payload["attachments"] = [
            SimpleUploadedFile(
                "program.exe",
                b"not allowed",
                content_type="application/octet-stream",
            )
        ]

        response = self.client.post(
            "/api/leads/",
            payload,
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(LeadAttachment.objects.count(), 0)
