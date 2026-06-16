"""
Idempotent production bootstrap. Safe to run on every deploy.

Seeds the chart of accounts + system accounts, the role groups, and (optionally)
creates/updates an admin superuser from environment variables:

    DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_PASSWORD
    DJANGO_SUPERUSER_EMAIL   (optional)
"""
import os
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed chart of accounts, roles, and ensure the admin user exists."

    def handle(self, *args, **options):
        self.stdout.write("Seeding chart of accounts…")
        call_command("seed_coa")
        self.stdout.write("Seeding roles…")
        call_command("seed_roles")

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        if username and password:
            from django.contrib.auth import get_user_model
            from django.contrib.auth.models import Group

            User = get_user_model()
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": email}
            )
            user.is_staff = True
            user.is_superuser = True
            if email:
                user.email = email
            user.set_password(password)
            user.save()
            sa = Group.objects.filter(name="Super Admin").first()
            if sa:
                user.groups.add(sa)
            self.stdout.write(self.style.SUCCESS(
                f"Admin user '{username}' {'created' if created else 'updated'}."
            ))
        else:
            self.stdout.write("DJANGO_SUPERUSER_* not set — skipping admin creation.")

        self.stdout.write(self.style.SUCCESS("Bootstrap complete."))
