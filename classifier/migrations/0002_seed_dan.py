from django.contrib.auth.hashers import make_password
from django.db import migrations

# Per the assignment: there is no self-serve signup anywhere in this project.
# The one required account is created here, idempotently, so it exists the
# moment `migrate` is run on a fresh database (including in Docker on AWS).
USERNAME = "dan"
PASSWORD = "Optimization1234"


def create_dan(apps, schema_editor):
    User = apps.get_model("auth", "User")
    if not User.objects.filter(username=USERNAME).exists():
        User.objects.create(
            username=USERNAME,
            password=make_password(PASSWORD),
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )


def remove_dan(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(username=USERNAME).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("classifier", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_dan, remove_dan),
    ]
