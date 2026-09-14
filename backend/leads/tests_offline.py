import csv
import io

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .admin import QUALIFIED_LEAD_TARGET
from .models import Lead


@override_settings(LEAD_NOTIFICATION_EMAILS=[])
class LeadMetrikaIdsApiTests(APITestCase):
    def post_lead(self, **extra):
        cache.clear()
        payload = {
            "phone": "+7 (916) 482-15-37",
            "consent_accepted": "true",
            "form_elapsed_ms": "9000",
            **extra,
        }
        return self.client.post(
            "/api/leads/",
            payload,
            format="multipart",
            HTTP_USER_AGENT="Mozilla/5.0 (Linux; Android 15) Chrome/126.0 Mobile",
        )

    def test_client_id_and_yclid_are_saved(self):
        response = self.post_lead(
            metrika_client_id="1789330831783517874",
            yclid="1920623584952695010",
        )

        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.get()
        self.assertEqual(lead.metrika_client_id, "1789330831783517874")
        self.assertEqual(lead.yclid, "1920623584952695010")
        self.assertEqual(lead.quality, Lead.Quality.UNCHECKED)
        self.assertNotIn("metrika_client_id", response.data)

    def test_garbage_ids_do_not_reject_lead(self):
        response = self.post_lead(metrika_client_id="<script>", yclid="a b;c")

        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.get()
        self.assertEqual(lead.metrika_client_id, "")
        self.assertEqual(lead.yclid, "")

    def test_old_form_without_ids_still_works(self):
        response = self.post_lead()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.get().metrika_client_id, "")


class OfflineConversionAdminTests(TestCase):
    def setUp(self):
        owner = get_user_model().objects.create_superuser(
            "owner", "owner@example.com", None
        )
        self.client.force_login(owner)
        self.url = reverse("admin:leads_lead_changelist")

    def run_action(self, action, leads):
        return self.client.post(
            self.url,
            {
                "action": action,
                "index": 0,
                "_selected_action": [lead.pk for lead in leads],
            },
        )

    def test_mark_real_and_fake(self):
        first = Lead.objects.create(phone="+7 (916) 482-15-37")
        second = Lead.objects.create(phone="+7 (926) 731-58-04")

        self.run_action("mark_real", [first])
        self.run_action("mark_fake", [second])

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.quality, Lead.Quality.REAL)
        self.assertEqual(second.quality, Lead.Quality.FAKE)

    def test_export_contains_only_real_leads_with_client_id(self):
        real = Lead.objects.create(
            phone="+7 (916) 482-15-37",
            quality=Lead.Quality.REAL,
            metrika_client_id="1789330831783517874",
        )
        real_without_id = Lead.objects.create(
            phone="+7 (926) 731-58-04", quality=Lead.Quality.REAL
        )
        fake = Lead.objects.create(
            phone="+7 (903) 264-90-18",
            quality=Lead.Quality.FAKE,
            metrika_client_id="1789237703900045426",
        )

        response = self.run_action(
            "export_offline_conversions", [real, real_without_id, fake]
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/csv"))
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
        self.assertEqual(rows[0], ["ClientId", "Target", "DateTime"])
        self.assertEqual(
            rows[1:],
            [
                [
                    "1789330831783517874",
                    QUALIFIED_LEAD_TARGET,
                    str(int(real.created_at.timestamp())),
                ]
            ],
        )

    def test_export_without_eligible_leads_returns_to_list(self):
        lead = Lead.objects.create(phone="+7 (916) 482-15-37")

        response = self.run_action("export_offline_conversions", [lead])

        self.assertEqual(response.status_code, 302)
