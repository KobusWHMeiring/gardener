import pytest
from core.models import Zone, Plant, GardenEvent, IngestQueue, FertilizerRecipe
from core.services.ingestion import ingest_media
from core.services.processing import process_ingest_item_multi

@pytest.mark.django_db
def test_full_garden_lifecycle():
    """
    Verifies the entire system flow from ingestion to event creation
    covering the full 'Seed to Removal' lifecycle.
    """
    # 1. Setup: Create a Zone
    zone = Zone.objects.create(
        name="North Bed", 
        sunlight_level=Zone.SunlightLevel.FULL_SUN,
        size_m2=10.5,
        irrigation_type=Zone.IrrigationType.DRIP
    )
    
    # 2. Setup: Fertilizer Recipe
    recipe = FertilizerRecipe.objects.create(
        name="Compost Tea",
        ingredients="Compost, Water, Molasses",
        instructions="Steep for 24 hours"
    )

    # 3. Lifecycle Test: Sow -> Germinate -> Transplant -> First Harvest -> Terminate
    plant = Plant.objects.create(name="Basil", zone=zone)
    assert plant.status == Plant.Status.SEEDLING

    # A. SOW
    ingest_sow = ingest_media(text_input="Sowed 20 basil seeds in a tray")
    process_ingest_item_multi(ingest_sow.id, {
        'zone_id': zone.id,
        'event_date': '2026-01-20',
        'actions': [{
            'plant_id': plant.id,
            'event_type': GardenEvent.EventType.SOW,
            'metadata': {'seed_count': 20, 'is_direct': False}
        }]
    })
    plant.refresh_from_db()
    assert plant.status == Plant.Status.SEEDLING
    
    event_sow = GardenEvent.objects.get(plant=plant, event_type=GardenEvent.EventType.SOW)
    assert event_sow.metadata['seed_count'] == 20
    assert event_sow.performed_at.date().isoformat() == '2026-01-20'

    # B. GERMINATE
    ingest_germ = ingest_media(text_input="15 basil seeds germinated")
    process_ingest_item_multi(ingest_germ.id, {
        'zone_id': zone.id,
        'actions': [{
            'plant_id': plant.id,
            'event_type': GardenEvent.EventType.GERMINATE,
            'metadata': {'germination_count': 15}
        }]
    })
    plant.refresh_from_db()
    assert plant.status == Plant.Status.GERMINATED

    # C. TRANSPLANT
    ingest_trans = ingest_media(text_input="Transplanted basil to the North Bed")
    process_ingest_item_multi(ingest_trans.id, {
        'zone_id': zone.id,
        'actions': [{
            'plant_id': plant.id,
            'event_type': GardenEvent.EventType.TRANSPLANT
        }]
    })
    plant.refresh_from_db()
    assert plant.status == Plant.Status.PLANTED

    # D. FERTILIZE
    ingest_fert = ingest_media(text_input="Fertilized basil with Compost Tea")
    process_ingest_item_multi(ingest_fert.id, {
        'zone_id': zone.id,
        'actions': [{
            'plant_id': plant.id,
            'event_type': GardenEvent.EventType.FERTILIZE,
            'metadata': {'recipe_id': recipe.id, 'application_method': 'Soil'}
        }]
    })
    # Note: No status change for fertilization

    # E. FIRST HARVEST
    ingest_harv = ingest_media(text_input="Picked the first basil leaves!")
    process_ingest_item_multi(ingest_harv.id, {
        'zone_id': zone.id,
        'actions': [{
            'plant_id': plant.id,
            'event_type': GardenEvent.EventType.FIRST_HARVEST
        }]
    })
    plant.refresh_from_db()
    assert plant.status == Plant.Status.PROVIDING

    # F. TERMINATE
    ingest_term = ingest_media(text_input="Basil removed at end of season")
    process_ingest_item_multi(ingest_term.id, {
        'zone_id': zone.id,
        'actions': [{
            'plant_id': plant.id,
            'event_type': GardenEvent.EventType.TERMINATE
        }]
    })
    plant.refresh_from_db()
    assert plant.status == Plant.Status.REMOVED

@pytest.mark.django_db
def test_multi_plant_ingestion():
    """Verify that multiple plants mentioned in one ingestion create multiple events."""
    zone = Zone.objects.create(name="Greenhouse")
    ingest = ingest_media(text_input="I planted 20 beans and 10 spinaches on 20 Jan 2026")
    
    # Simulate what the UI sends for multi-action
    process_ingest_item_multi(ingest.id, {
        'zone_id': zone.id,
        'event_date': '2026-01-20',
        'actions': [
            {
                'new_plant_name': 'Bean',
                'event_type': GardenEvent.EventType.SOW,
                'metadata': {'seed_count': 20}
            },
            {
                'new_plant_name': 'Spinach',
                'event_type': GardenEvent.EventType.SOW,
                'metadata': {'seed_count': 10}
            }
        ]
    })

    assert Plant.objects.count() == 2
    assert GardenEvent.objects.count() == 2
    # Auto-naming: Bean - 2026-01-20
    assert GardenEvent.objects.filter(plant__name='Bean - 2026-01-20', metadata__seed_count=20).exists()
    assert GardenEvent.objects.filter(plant__name='Spinach - 2026-01-20', metadata__seed_count=10).exists()

@pytest.mark.django_db
def test_transplant_zone_change():
    """Verify that transplanting a plant moves it to a new zone and updates status."""
    greenhouse = Zone.objects.create(name="Greenhouse")
    garden = Zone.objects.create(name="Garden")
    
    # 1. Start in Greenhouse
    plant = Plant.objects.create(name="Spinach", zone=greenhouse, status=Plant.Status.SEEDLING)
    
    ingest = ingest_media(text_input="Transplanted spinach from greenhouse to garden")
    
    # 2. Transplant to Garden
    process_ingest_item_multi(ingest.id, {
        'zone_id': garden.id,
        'actions': [{
            'plant_id': plant.id,
            'event_type': GardenEvent.EventType.TRANSPLANT
        }]
    })
    
    plant.refresh_from_db()
    assert plant.zone == garden
    assert plant.status == Plant.Status.PLANTED
    
    # 3. Verify event is recorded in the new zone
    event = GardenEvent.objects.get(plant=plant, event_type=GardenEvent.EventType.TRANSPLANT)
    assert event.zone == garden