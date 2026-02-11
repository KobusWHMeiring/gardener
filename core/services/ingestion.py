from core.models import IngestQueue
from .enrichment import enrich_ingest_item

def ingest_media(file_obj=None, text_input=None, audio_file=None):
    """
    Ingests raw media (file), text input, or audio file into the IngestQueue.
    """
    if not file_obj and not audio_file and not (text_input and text_input.strip()):
        return None

    ingest_item = IngestQueue.objects.create(
        source_file=file_obj,
        audio_file=audio_file,
        raw_text=text_input or ""
    )
    
    # Trigger AI enrichment
    enrich_ingest_item(ingest_item.id)
    ingest_item.refresh_from_db()
    print('ingested item')
    print(ingest_item)
    return ingest_item
