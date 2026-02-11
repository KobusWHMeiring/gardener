import pytest
from django.urls import reverse
from core.models import Zone, Plant, GardenEvent, IngestQueue, Species

@pytest.mark.django_db
def test_broccoli_alfalfa_ingestion_full_flow(client):
    """Verify that multiple new plants in one ingestion are correctly created via the view."""
    zone = Zone.objects.create(name="Greenhouse")
    ingest = IngestQueue.objects.create(raw_text="Planted broccoli and alfalfa")
    
    # Simulate what the browser sends
    url = reverse('confirm_ingest', kwargs={'ingest_id': ingest.id})
    post_data = {
        'zone_id': zone.id,
        'event_date': '2026-01-25',
        # Action 0: Broccoli
        'action_0_event_type': 'PLANT',
        'action_0_plant_id': '', # New plant
        'action_0_species_id': '', # Let it auto-create or match name
        'action_0_new_plant_name': 'broccoli',
        'action_0_meta_seed_count': '50',
        # Action 1: Alfalfa
        'action_1_event_type': 'PLANT',
        'action_1_plant_id': '', # New plant
        'action_1_species_id': '', # Let it auto-create or match name
        'action_1_new_plant_name': 'alfalfa',
        'action_1_meta_seed_count': '50',
    }
    
    response = client.post(url, post_data)
    assert response.status_code == 200
    
    assert Plant.objects.count() == 2
    assert GardenEvent.objects.count() == 2
    
    plants = list(Plant.objects.all().order_by('name'))
    # broccoli - 2026-01-25 comes before alfalfa? No, a comes before b.
    # alfalfa - 2026-01-25
    # broccoli - 2026-01-25
    assert plants[0].name == 'alfalfa - 2026-01-25'
    assert plants[1].name == 'broccoli - 2026-01-25'
