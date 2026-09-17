import io

from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from content.models import Review

from .crypto import PREFIX, UnreadablePhone
from .models import Lead


PHONE = "+7 (916) 482-15-37"


def raw_phones():
    """Телефоны так, как они лежат в базе, минуя расшифровку."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT phone FROM leads_lead ORDER BY id")
        return [row[0] for row in cursor.fetchall()]


@override_settings(LEAD_NOTIFICATION_EMAILS=[])
class LeadMinimalDataTests(APITestCase):
    def post_lead(self, **extra):
        cache.clear()
        payload = {
            "phone": PHONE,
            "message": "Баня 6х4",
            "consent_accepted": "true",
            "consent_version": "2026-09-17",
            "form_elapsed_ms": "9000",
            "page_url": "https://brusodel.ru/projects/banya-bb-01?utm_source=yandex&yclid=123#prices",
            **extra,
        }
        return self.client.post(
            "/api/leads/",
            payload,
            format="multipart",
            HTTP_USER_AGENT="Mozilla/5.0 (Linux; Android 15) Chrome/126.0 Mobile",
            REMOTE_ADDR="203.0.113.10",
        )

    def test_only_minimal_fields_exist(self):
        stored = {field.name for field in Lead._meta.concrete_fields}
        self.assertEqual(
            stored,
            {
                "id",
                "phone",
                "message",
                "source",
                "project",
                "page_url",
                "consent_version",
                "consent_given_at",
                "is_processed",
                "manager_comment",
                "anonymized_at",
                "created_at",
                "updated_at",
            },
        )

    def test_tracking_fields_from_old_form_are_ignored(self):
        response = self.post_lead(
            utm_source="yandex",
            utm_term="баня из бруса",
            yclid="1920623584952695010",
            metrika_client_id="1789330831783517874",
        )

        self.assertEqual(response.status_code, 201)
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM leads_lead")
            row = " ".join(str(value) for value in cursor.fetchone())
        for leaked in ("yandex", "1920623584952695010", "1789330831783517874", "203.0.113.10", "Android"):
            self.assertNotIn(leaked, row)

    def test_page_url_keeps_only_the_page(self):
        self.post_lead()

        self.assertEqual(
            Lead.objects.get().page_url,
            "https://brusodel.ru/projects/banya-bb-01",
        )

    @override_settings(LEAD_PHONE_ENCRYPTION_KEY="test-only-key")
    def test_phone_is_encrypted_in_database(self):
        self.post_lead()

        [raw] = raw_phones()
        self.assertTrue(raw.startswith(PREFIX))
        self.assertNotIn("482-15-37", raw)
        self.assertEqual(Lead.objects.get().phone, PHONE)

    def test_without_key_phone_is_stored_readable(self):
        self.post_lead()

        self.assertEqual(raw_phones(), [PHONE])
        self.assertEqual(Lead.objects.get().phone, PHONE)

    @override_settings(LEAD_NOTIFICATION_EMAILS=["manager@example.com"])
    def test_manager_email_has_only_what_is_needed(self):
        self.post_lead()

        body = mail.outbox[0].body
        self.assertIn(PHONE, body)
        self.assertIn("Баня 6х4", body)
        self.assertIn("https://brusodel.ru/projects/banya-bb-01", body)
        for leaked in ("IP", "User-Agent", "utm", "yclid", "203.0.113.10", "Согласие"):
            self.assertNotIn(leaked, body)


class PhoneEncryptionStorageTests(TestCase):
    def test_encrypt_command_encrypts_existing_plain_phones(self):
        Lead.objects.create(phone=PHONE)

        with override_settings(LEAD_PHONE_ENCRYPTION_KEY="test-only-key"):
            call_command("encrypt_lead_phones", stdout=io.StringIO())
            [raw] = raw_phones()
            self.assertTrue(raw.startswith(PREFIX))
            self.assertEqual(Lead.objects.get().phone, PHONE)

    def test_encrypt_command_requires_key(self):
        with self.assertRaises(CommandError):
            call_command("encrypt_lead_phones")

    def test_saving_with_wrong_key_keeps_original_phone(self):
        with override_settings(LEAD_PHONE_ENCRYPTION_KEY="right-key"):
            lead = Lead.objects.create(phone=PHONE)
        [original_raw] = raw_phones()

        with override_settings(LEAD_PHONE_ENCRYPTION_KEY="wrong-key"):
            with self.assertLogs("leads.crypto", level="ERROR"):
                lead = Lead.objects.get(pk=lead.pk)
            self.assertIsInstance(lead.phone, UnreadablePhone)
            lead.is_processed = True
            lead.save()

        self.assertEqual(raw_phones(), [original_raw])
        with override_settings(LEAD_PHONE_ENCRYPTION_KEY="right-key"):
            self.assertEqual(Lead.objects.get(pk=lead.pk).phone, PHONE)

    def test_admin_log_title_has_no_phone(self):
        lead = Lead.objects.create(phone=PHONE)

        self.assertNotIn("482", str(lead))


class ReviewAuthorMaskingTests(APITestCase):
    def test_api_shows_first_name_and_initial(self):
        Review.objects.create(author_name="Андрей Кузнецов", city="Москва", text="Отличная баня")
        Review.objects.create(author_name="Ирина", city="Кострома", text="Спасибо")

        response = self.client.get("/api/reviews/")

        names = sorted(review["author_name"] for review in response.data)
        self.assertEqual(names, ["Андрей К.", "Ирина"])
        self.assertNotIn("Кузнецов", response.content.decode("utf-8"))
