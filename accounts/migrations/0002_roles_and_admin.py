import os

from django.contrib.auth.hashers import make_password
from django.db import migrations

ADMIN_GROUP = "Administrator"
CUSTOMER_GROUP = "Customer"


def create_roles_and_admin(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("accounts", "User")

    admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
    Group.objects.get_or_create(name=CUSTOMER_GROUP)

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@megano.local")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")

    if not User.objects.filter(username=username).exists():
        admin = User.objects.create(
            username=username,
            email=email,
            full_name="Administrator",
            password=make_password(password),
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        admin.groups.add(admin_group)


def remove_roles_and_admin(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("accounts", "User")

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    User.objects.filter(username=username, is_superuser=True).delete()
    Group.objects.filter(name__in=[ADMIN_GROUP, CUSTOMER_GROUP]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_roles_and_admin, remove_roles_and_admin),
    ]
