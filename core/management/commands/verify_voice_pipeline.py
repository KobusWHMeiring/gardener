import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files import File
from core.models import IngestQueue
from core.services.enrichment import enrich_ingest_item

class Command(BaseCommand):
    help = 'Verify the voice ingestion pipeline with a real audio file.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to the audio file to test')
        parser.add_argument('--dry-run', action='store_true', help='Rollback transaction after test')

    def handle(self, *args, **options):
        file_path = options.get('file')
        dry_run = options.get('dry_run')

        if not file_path:
            self.stdout.write(self.style.ERROR("Please provide a file path using --file"))
            return

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with transaction.atomic():
                self.stdout.write(f"Creating IngestQueue record for {file_path}...")
                
                ingest_item = IngestQueue.objects.create()
                with open(file_path, 'rb') as f:
                    ingest_item.audio_file.save(os.path.basename(file_path), File(f), save=True)

                self.stdout.write("Calling Gemini API for enrichment...")
                enrich_ingest_item(ingest_item.id)
                
                # Refresh from DB
                ingest_item.refresh_from_db()

                self.stdout.write("\n" + "="*40)
                self.stdout.write(self.style.SUCCESS("VERIFICATION REPORT"))
                self.stdout.write("="*40)
                self.stdout.write(f"Database ID: {ingest_item.id}")
                self.stdout.write(f"Raw Text: {ingest_item.raw_text}")
                self.stdout.write(f"Cleaned Transcript: {ingest_item.transcript_clean}")
                self.stdout.write(f"Predicted Action: {ingest_item.predicted_action}")
                
                payload = ingest_item.predicted_data.get('extracted_data', {})
                self.stdout.write("Extracted Payload:")
                self.stdout.write(json.dumps(payload, indent=2))
                
                if dry_run:
                    self.stdout.write(self.style.WARNING("\nDry-run enabled. Rolling back transaction..."))
                    transaction.set_rollback(True)
                else:
                    self.stdout.write(self.style.SUCCESS("\nTransaction committed."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
            import traceback
            traceback.print_exc()
