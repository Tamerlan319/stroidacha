from decimal import Decimal

from rest_framework import serializers


class CalculatorRequestSerializer(serializers.Serializer):
    area = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal("1"))
    width = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=Decimal("2"))
    length = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=Decimal("2"))
    floors = serializers.ChoiceField(choices=("1", "1.5", "2"))
    material = serializers.SlugField()
    package = serializers.SlugField(required=False, allow_blank=True, default="")
    project = serializers.CharField(required=False, allow_blank=True, default="")
    price_date = serializers.DateField(required=False, allow_null=True)

    bedrooms = serializers.IntegerField(min_value=1, max_value=20, required=False, allow_null=True)

    first_floor_area_m2 = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    mansard_area_m2 = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    second_floor_area_m2 = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )

    external_wall_length_m = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    external_wall_height_m = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    external_openings_area_m2 = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    external_wall_volume_m3 = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0"), required=False, allow_null=True
    )

    internal_wall_length_m = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    internal_wall_height_m = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    internal_openings_area_m2 = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    internal_wall_volume_m3 = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0"), required=False, allow_null=True
    )

    beams_volume_m3 = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0"), required=False, allow_null=True
    )
    rafters_volume_m3 = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0"), required=False, allow_null=True
    )
    lathing_volume_m3 = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0"), required=False, allow_null=True
    )
    other_structural_lumber_volume_m3 = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0"), required=False, allow_null=True
    )
    # Старый агрегированный параметр поддерживается для совместимости.
    structural_lumber_volume_m3 = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0"), required=False, allow_null=True
    )

    terrace_area = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )

    foundation = serializers.SlugField(required=False, allow_blank=True, default="")
    foundation_pile_count = serializers.IntegerField(min_value=1, max_value=1000, required=False, allow_null=True)

    roof = serializers.SlugField(required=False, allow_blank=True, default="")
    roof_area = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("1"), required=False, allow_null=True
    )
    gable_area = serializers.DecimalField(
        max_digits=9, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    roof_shape = serializers.ChoiceField(
        choices=("gable", "hip", "mansard", "complex", "other"),
        required=False,
        allow_blank=True,
        default="",
    )
    roof_pitch_deg = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("1"),
        max_value=Decimal("80"),
        required=False,
        allow_null=True,
    )
    roof_overhang_m = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=Decimal("3"),
        required=False,
        allow_null=True,
    )
    roof_complexity_factor = serializers.DecimalField(
        max_digits=5,
        decimal_places=3,
        min_value=Decimal("0.5"),
        max_value=Decimal("3"),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        area = Decimal(attrs["area"])
        width = Decimal(attrs["width"])
        length = Decimal(attrs["length"])
        floors = Decimal(str(attrs["floors"]))
        footprint = width * length

        max_ratio = {
            Decimal("1"): Decimal("1.05"),
            Decimal("1.5"): Decimal("2.05"),
            Decimal("2"): Decimal("2.05"),
        }[floors]
        if area > footprint * max_ratio:
            raise serializers.ValidationError(
                f"Площадь {area:g} м² не соответствует дому {width:g}×{length:g} м "
                f"при этажности {floors:g}. Проверьте площадь, размеры или этажность."
            )

        if floors == Decimal("1") and area > footprint * Decimal("1.05"):
            raise serializers.ValidationError(
                "Для одноэтажного дома общая площадь не может превышать пятно застройки."
            )

        floor_parts = [
            attrs.get("first_floor_area_m2"), attrs.get("mansard_area_m2"), attrs.get("second_floor_area_m2")
        ]
        if any(value is not None for value in floor_parts):
            total_parts = sum((Decimal(value or 0) for value in floor_parts), Decimal("0"))
            if abs(total_parts - area) > Decimal("1.0"):
                raise serializers.ValidationError(
                    "Сумма явно заданных площадей этажей должна совпадать с общей площадью (допуск 1 м²)."
                )

        roof_shape = attrs.get("roof_shape")
        if roof_shape and roof_shape != "gable" and attrs.get("roof_area") is None:
            raise serializers.ValidationError(
                "Для ломаной/вальмовой/сложной крыши укажите фактическую площадь roof_area. "
                "Автоматическая геометрия применяется только к простой двускатной крыше."
            )
        return attrs
