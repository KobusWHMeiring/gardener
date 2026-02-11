import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect
from core.models import Zone, Species, Plant, GardenEvent, IngestQueue
import json
from asgiref.sync import sync_to_async # Import sync_to_async

@pytest.mark.django_db(transaction=True)
async def test_multi_plant_ingestion_e2e(live_server, page: Page): # Make the test function async
    """
    E2E test for multi-plant ingestion flow.
    Verifies that clicking 'Ingest' shows the inbox card, 
    and 'Confirm' creates both plants and refreshes history.
    """
    # 1. Setup Data
    zone = await sync_to_async(Zone.objects.create)(name="Top Garden")
    await sync_to_async(Species.objects.create)(name="zucchini")
    await sync_to_async(Species.objects.create)(name="pumpkin")
    print(f"DEBUG: Setup complete. Species count: {await sync_to_async(Species.objects.count)()}")

    # 2. Navigate to Dashboard
    page.goto(live_server.url + reverse('dashboard'))
    
    # 3. Type ingestion text
    textarea = page.locator('textarea[name="text_input"]')
    textarea.fill("I planted zucchini and pumpkins, 10 seeds each directly in the top garden")
    
    # 4. Mock the enrichment result
    predicted_data = {
        "engine": "gemini-2.0-flash", 
        "extracted_data": {
            "event_date": "2026-01-21", 
            "predicted_zone": "Top Garden", 
            "actions": [
                {"event_type": "SOW", "plant_name": "zucchini", "plant_id": None, "species_id": None, "source_zone_id": None, "metadata": {"is_direct": True, "seed_count": 10}}, 
                {"event_type": "SOW", "plant_name": "pumpkin", "plant_id": None, "species_id": None, "source_zone_id": None, "metadata": {"is_direct": True, "seed_count": 10}}
            ]
        }, 
        "predicted_date": "2026-01-21", 
        "predicted_zone_name": "Top Garden", 
        "actions": [
            {"event_type": "SOW", "plant_name": "zucchini", "plant_id": None, "species_id": None, "source_zone_id": None, "metadata": {"is_direct": True, "seed_count": 10}}, 
            {"event_type": "SOW", "plant_name": "pumpkin", "plant_id": None, "species_id": None, "source_zone_id": None, "metadata": {"is_direct": True, "seed_count": 10}}
        ]
    }
    
    # Pre-create the item so it shows up in the inbox
    item = await sync_to_async(IngestQueue.objects.create)(
        raw_text="Manual trigger test",
        predicted_data=predicted_data,
        processed=False
    )
    
    page.goto(live_server.url + reverse('dashboard'))

    # 5. Verify Inbox Card appears
    inbox_card = page.locator(f"#ingest-{item.id}")
    expect(inbox_card).to_be_visible()

    # 6. Click "Confirm All Events"
    confirm_btn = inbox_card.locator('button[type="submit"]')
    confirm_btn.click()
    print("DEBUG: Clicked confirm button.")
    
    # 7. Verify Inbox Card disappears (HTMX swap)
    expect(inbox_card).not_to_be_visible()
    print(f"DEBUG: Card disappeared. Plant count: {await sync_to_async(Plant.objects.count)()}")
    
    # 8. Verify DB records
    # Using a short wait for the DB to update because it's async from the browser's perspective
    page.wait_for_timeout(1000)
    assert await sync_to_async(Plant.objects.count)() == 2
    assert await sync_to_async(GardenEvent.objects.count)() == 2