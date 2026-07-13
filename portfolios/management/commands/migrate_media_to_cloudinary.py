"""
Run: python manage.py migrate_media_to_cloudinary

Uploads existing local media files (CVs, profile images) to Cloudinary.
Idempotent — skips files that already exist on Cloudinary.
"""

import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from portfolios.models import Profile


class Command(BaseCommand):
    help = "Migrate existing local media files to Cloudinary"

    def handle(self, *args, **options):
        profiles = Profile.objects.all()
        migrated = 0
        skipped = 0
        errors = 0

        for profile in profiles:
            for field_name in ('cv_file', 'profile_image'):
                field_file = getattr(profile, field_name, None)
                if not field_file or not field_file.name:
                    continue

                local_path = os.path.join(settings.MEDIA_ROOT, field_file.name)
                if not os.path.exists(local_path):
                    self.stdout.write(f"  [SKIP] Local file not found: {local_path}")
                    skipped += 1
                    continue

                if default_storage.exists(field_file.name):
                    self.stdout.write(f"  [SKIP] Already on Cloudinary: {field_file.name}")
                    skipped += 1
                    continue

                try:
                    with open(local_path, 'rb') as f:
                        file_bytes = f.read()

                    filename = os.path.basename(field_file.name)
                    upload_path = field_file.name

                    default_storage.save(upload_path, ContentFile(file_bytes))
                    self.stdout.write(self.style.SUCCESS(f"  [OK] Uploaded: {upload_path}"))
                    migrated += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"  [ERR] Failed {field_file.name}: {e}"))
                    errors += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Migrated={migrated}, Skipped={skipped}, Errors={errors}"
        ))
