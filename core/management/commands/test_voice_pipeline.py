from django.core.management.base import BaseCommand
from core.services.ingestion import ingest_media
from core.models import IngestQueue
import time

class Command(BaseCommand):
    help = 'Tests the voice ingestion logic (text-only simulation for prompt verification)'

    def handle(self, *args, **options):
        self.stdout.write("Simulating voice-style text ingestion...")
        
        # Simulating a "messy" transcript that needs cleaning
        text = "Umm, okay, so I just sowed some Spinach in the Greenhouse today, and uh, also watered the Tomatoes in the Garden."
        
        ingest_item = ingest_media(text_input=text)
        
        self.stdout.write(self.style.SUCCESS(f"Created IngestQueue item: {ingest_item.id}"))
        self.stdout.write(f"Raw Text: {ingest_item.raw_text}")
        self.stdout.write(f"Cleaned Transcript: {ingest_item.transcript_clean}")
        self.stdout.write(f"Predicted Action: {ingest_item.predicted_action}")
        self.stdout.write(f"Actions found: {len(ingest_item.predicted_data.get('actions', []))}")
        
        for idx, action in enumerate(ingest_item.predicted_data.get('actions', [])):
            self.stdout.write(f"  Action {idx+1}: {action.get('event_type')} - {action.get('plant_name')}")
