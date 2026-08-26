from decimal import Decimal

from django.test import TestCase

from .models import Project, ProjectCategory


class ComputedSizeTextTests(TestCase):
    """width/length хранятся как NUMERIC(6,2), поэтому Decimal всегда
    приходит с двумя знаками после точки. computed_size_text должен
    показывать "6х7", а не "6.00х7.00" — см. commit message."""

    def setUp(self):
        self.category = ProjectCategory.objects.create(title="Дома", slug="houses-size-text")

    def make_project(self, width, length):
        return Project.objects.create(
            title=f"Тест {width}x{length}",
            category=self.category,
            width=Decimal(width),
            length=Decimal(length),
        )

    def test_strips_trailing_zeros_for_whole_numbers(self):
        project = self.make_project("6.00", "7.00")
        self.assertEqual(project.computed_size_text, "6х7")

    def test_keeps_a_single_meaningful_decimal(self):
        project = self.make_project("9.50", "10.00")
        self.assertEqual(project.computed_size_text, "9.5х10")

    def test_does_not_use_scientific_notation_for_round_tens(self):
        project = self.make_project("60.00", "20.00")
        self.assertEqual(project.computed_size_text, "60х20")

    def test_falls_back_to_size_text_when_dimensions_missing(self):
        project = Project.objects.create(
            title="Без размеров",
            category=self.category,
            size_text="6х6 (уточняется)",
        )
        self.assertEqual(project.computed_size_text, "6х6 (уточняется)")
