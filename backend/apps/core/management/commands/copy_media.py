"""Copy every file referenced by the database from a local folder into the configured default storage.

Used to move a seeded catalog to a host whose MEDIA_STORAGE=db:

    python manage.py copy_media --source ./media
"""

from pathlib import Path

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db.models import FileField


class Command(BaseCommand):
    help = "Upload files referenced by FileFields from --source into default_storage (skips existing)."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, help="Local media directory.")

    def handle(self, *args, source, **options):
        root = Path(source)
        if not root.is_dir():
            raise CommandError(f"{root} is not a directory.")

        names = set()
        for model in apps.get_models():
            for field in model._meta.get_fields():
                if isinstance(field, FileField):
                    names.update(n for n in model.objects.values_list(field.name, flat=True) if n)

        copied = missing = 0
        for name in sorted(names):
            path = root / name
            if default_storage.exists(name):
                continue
            if not path.is_file():
                self.stderr.write(f"missing locally: {name}")
                missing += 1
                continue
            default_storage._save(name, ContentFile(path.read_bytes(), name=path.name))
            copied += 1
        self.stdout.write(self.style.SUCCESS(f"Copied {copied} files ({missing} missing, {len(names)} referenced)."))
