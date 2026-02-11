import pytest
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from core.models import Zone, Plant, GardenEvent, IngestQueue
from core.services.ingestion import ingest_media
from core.services.processing import process_ingest_item

@pytest.mark.django_db
def test_timestamped_model_behavior():
    """Verify that saving any model automatically populates created_at and updated_at."""
    zone = Zone.objects.create(name="Front Yard", sunlight_level=Zone.SunlightLevel.FULL_SUN)
    assert zone.created_at is not None
    assert zone.updated_at is not None
    
    original_updated_at = zone.updated_at
    zone.name = "Back Yard"
    zone.save()
    
    assert zone.updated_at > original_updated_at

@pytest.mark.django_db
def test_gardenevent_without_plant():
    """Verify that a GardenEvent can be created for a Zone without requiring a specific Plant."""
    zone = Zone.objects.create(name="Greenhouse")
    event = GardenEvent.objects.create(
        zone=zone,
        event_type=GardenEvent.EventType.WATER
    )
    assert event.id is not None
    assert event.plant is None
    assert event.zone == zone

@pytest.mark.django_db
def test_ingestqueue_defaults():
    """Verify IngestQueue defaults processed to False."""
    item = IngestQueue.objects.create(raw_text="Test ingestion")
    assert item.processed is False
    assert item.predicted_data == {}

@pytest.mark.django_db
def test_plant_status_choices():
    """Verify Plant model choices."""
    zone = Zone.objects.create(name="Test Zone")
    plant = Plant.objects.create(name="Tomato", zone=zone, status=Plant.Status.SEEDLING)
    assert plant.status == "SEEDLING"

@pytest.mark.django_db
def test_ingest_media_service():
    """Verify ingest_media creates an IngestQueue item and triggers enrichment."""
    dummy_file = SimpleUploadedFile("test.txt", b"dummy content")
    item = ingest_media(file_obj=dummy_file, text_input="I watered the plants")
    assert item.id is not None
    assert item.raw_text == "I watered the plants"
    assert item.predicted_action == "WATER"

@pytest.mark.django_db
def test_process_ingest_item_service_success():
    """Verify process_ingest_item creates a GardenEvent and marks ingest as processed."""
    zone = Zone.objects.create(name="Garden")
    plant = Plant.objects.create(name="Basil", zone=zone)
    ingest = IngestQueue.objects.create(raw_text="I watered the basil")
    
    verified_data = {
        'plant_id': plant.id,
        'zone_id': zone.id,
        'event_type': GardenEvent.EventType.WATER
    }
    
    event = process_ingest_item(ingest.id, verified_data)
    
    ingest.refresh_from_db()
    assert event.id is not None
    assert event.plant == plant
    assert ingest.processed is True

@pytest.mark.django_db
def test_process_ingest_item_validation_failure():
    """Verify validation fails if plant does not belong to the zone."""
    zone1 = Zone.objects.create(name="Zone 1")
    zone2 = Zone.objects.create(name="Zone 2")
    plant = Plant.objects.create(name="Basil", zone=zone1)
    ingest = IngestQueue.objects.create(raw_text="Testing error")
    
    verified_data = {
        'plant_id': plant.id,
        'zone_id': zone2.id,
        'event_type': GardenEvent.EventType.WATER
    }
    
    with pytest.raises(ValidationError):
        process_ingest_item(ingest.id, verified_data)
    
    ingest.refresh_from_db()
    assert ingest.processed is False

@pytest.mark.django_db
def test_dashboard_view(client):
    """Verify dashboard loads and displays items."""
    zone = Zone.objects.create(name="Backyard")
    IngestQueue.objects.create(raw_text="Pending task")
    GardenEvent.objects.create(zone=zone, event_type=GardenEvent.EventType.WATER)
    
    response = client.get(reverse('dashboard'))
    assert response.status_code == 200
    assert "Pending task" in response.content.decode()
    assert "Backyard" in response.content.decode()

@pytest.mark.django_db
def test_confirm_ingest_view(client):
    """Verify confirm_ingest view processes item and returns empty response with trigger."""
    zone = Zone.objects.create(name="Backyard")
    ingest = IngestQueue.objects.create(raw_text="Watered backyard")
    
    url = reverse('confirm_ingest', args=[ingest.id])
    # Now expects action-prefixed fields
    data = {
        'zone_id': zone.id,
        'action_0_event_type': 'WATER'
    }
    
    response = client.post(url, data)
    assert response.status_code == 200
    assert response.content == b""
    assert response['HX-Trigger'] == 'eventConfirmed'
    
    ingest.refresh_from_db()
    assert ingest.processed is True
    assert GardenEvent.objects.filter(zone=zone, event_type='WATER').exists()

@pytest.mark.django_db
def test_ingest_view_htmx(client):
    """Verify ingest_view creates item and returns partial."""
    Zone.objects.create(name="Garden")
    url = reverse('ingest_media')
    data = {'text_input': 'Harvested tomatoes'}
    
    response = client.post(url, data)
    assert response.status_code == 200
    # In multi-action, predictions are nested in actions
    assert "Harvested tomatoes" in response.content.decode()
    assert "HARVEST" in response.content.decode() 
    
    assert IngestQueue.objects.filter(raw_text='Harvested tomatoes').exists()


@pytest.mark.django_db
def test_ingest_delete_removes_pending_item(client):
    item = IngestQueue.objects.create(raw_text="Weeded beds")
    url = reverse('ingest_delete', args=[item.id])

    response = client.post(url, HTTP_HX_REQUEST='true')

    assert response.status_code == 200
    assert response.content == b""
    assert response.headers.get('HX-Trigger') == 'ingestItemDeleted'
    assert not IngestQueue.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_ingest_delete_processed_item_returns_error(client):
    item = IngestQueue.objects.create(raw_text="Already done", processed=True)
    url = reverse('ingest_delete', args=[item.id])

    response = client.post(url, HTTP_HX_REQUEST='true')

    assert response.status_code == 400
    assert IngestQueue.objects.filter(id=item.id).exists()
    assert "cannot be deleted" in response.content.decode()


@pytest.mark.django_db
def test_zone_detail_htmx_returns_partial(client):
    zone = Zone.objects.create(name="Herb Patch")
    url = reverse('garden_detail', args=[zone.id])

    idle_response = client.get(url, HTTP_HX_REQUEST='true')
    idle_body = idle_response.content.decode()
    assert idle_response.status_code == 200
    assert '<div id="zone-details-card"' in idle_body
    assert '<html' not in idle_body.lower()
    assert 'Edit Zone' in idle_body

    editing_response = client.get(url, {'edit': 'true'}, HTTP_HX_REQUEST='true')
    editing_body = editing_response.content.decode()
    assert editing_response.status_code == 200
    assert 'Cancel' in editing_body
    assert '<html' not in editing_body.lower()
