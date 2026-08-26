import json
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from .captcha import verify_smartcaptcha
from .models import Lead


class FakeUrlopenResponse(BytesIO):
    """Достаточно похоже на http.client.HTTPResponse для urllib.request.urlopen
    как контекстного менеджера: нужен только .read()."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def fake_urlopen(payload):
    def _call(url, timeout=None):
        return FakeUrlopenResponse(json.dumps(payload).encode("utf-8"))

    return _call


class VerifySmartcaptchaTests(TestCase):
    @override_settings(SMARTCAPTCHA_SERVER_KEY="")
    def test_disabled_when_no_server_key_configured(self):
        # Пустой токен тоже проходит — фича полностью выключена без ключа,
        # иначе локальная разработка и CI сломались бы без реального ключа.
        self.assertTrue(verify_smartcaptcha("", "127.0.0.1"))

    @override_settings(SMARTCAPTCHA_SERVER_KEY="test-secret")
    def test_empty_token_rejected_without_network_call(self):
        with patch("leads.captcha.urllib.request.urlopen") as mocked:
            self.assertFalse(verify_smartcaptcha("", "127.0.0.1"))
            mocked.assert_not_called()

    @override_settings(SMARTCAPTCHA_SERVER_KEY="test-secret")
    def test_accepts_ok_status_from_yandex(self):
        with patch(
            "leads.captcha.urllib.request.urlopen",
            side_effect=fake_urlopen({"status": "ok"}),
        ):
            self.assertTrue(verify_smartcaptcha("valid-token", "127.0.0.1"))

    @override_settings(SMARTCAPTCHA_SERVER_KEY="test-secret")
    def test_rejects_failed_status_from_yandex(self):
        with patch(
            "leads.captcha.urllib.request.urlopen",
            side_effect=fake_urlopen({"status": "failed", "message": "invalid-token"}),
        ):
            self.assertFalse(verify_smartcaptcha("bad-token", "127.0.0.1"))

    @override_settings(SMARTCAPTCHA_SERVER_KEY="test-secret")
    def test_fails_closed_on_network_error(self):
        with patch(
            "leads.captcha.urllib.request.urlopen",
            side_effect=TimeoutError("network is down"),
        ):
            self.assertFalse(verify_smartcaptcha("some-token", "127.0.0.1"))


@override_settings(SMARTCAPTCHA_SERVER_KEY="test-secret")
class LeadApiSmartcaptchaGateTests(APITestCase):
    """Проверка, что LeadCreateSerializer реально дёргает верификацию, а не
    только что сама функция верификации работает изолированно."""

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

    def test_rejects_lead_when_captcha_verification_fails(self):
        payload = self.valid_payload()
        payload["smartcaptcha_token"] = "bad-token"

        with patch("leads.serializers.verify_smartcaptcha", return_value=False):
            response = self.client.post("/api/leads/", payload, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertIn("smartcaptcha_token", response.data)
        self.assertEqual(Lead.objects.count(), 0)

    def test_accepts_lead_when_captcha_verification_succeeds(self):
        payload = self.valid_payload()
        payload["smartcaptcha_token"] = "good-token"

        with patch("leads.serializers.verify_smartcaptcha", return_value=True) as mocked:
            response = self.client.post("/api/leads/", payload, format="multipart")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.count(), 1)
        mocked.assert_called_once()
        self.assertEqual(mocked.call_args.args[0], "good-token")
