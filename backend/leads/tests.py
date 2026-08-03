import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Lead, LeadAttachment


class LeadApiComplianceTests(APITestCase):
    def setUp(self):
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
