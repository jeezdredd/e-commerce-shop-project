from django.db import migrations


def create_delivery_settings(apps, schema_editor):
    DeliverySettings = apps.get_model("orders", "DeliverySettings")
    DeliverySettings.objects.get_or_create(
        pk=1,
        defaults={
            "express_price": 500,
            "free_threshold": 2000,
            "base_delivery_price": 200,
        },
    )


def remove_delivery_settings(apps, schema_editor):
    DeliverySettings = apps.get_model("orders", "DeliverySettings")
    DeliverySettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_delivery_settings, remove_delivery_settings),
    ]
