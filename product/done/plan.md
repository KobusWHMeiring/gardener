 Garden Data Centralization
1. The Schema (Phase 1)
Base Model: Define core.models.TimeStampedModel (Abstract) containing created_at and updated_at. All models below inherit from this.
New Models:
Zone: name (Char), sunlight_level (TextChoices: Full Sun, Partial, Shade).
Plant: name (Char), zone (FK -> Zone), status (TextChoices: Seedling, Vegetative, Flowering, Harvested, Dead).
IngestQueue:
source_file (FileField, upload_to='uploads/%Y/%m/').
raw_text (TextField, blank=True).
predicted_action (Char, blank=True).
predicted_data (JSONField, default=dict).
processed (Boolean, default=False).
GardenEvent:
plant (FK -> Plant, null=True, blank=True).
zone (FK -> Zone).
event_type (TextChoices: Water, Plant, Seed, Note, Harvest, Fertilize).
performed_at (DateTime, default=now).
metadata (JSONField, default=dict).
Field Changes: N/A (Greenfield project).
Migration Strategy: makemigrations and migrate to initialize the schema.
2. The Logic (Phase 2 - core/services/)
Service Function 1: ingest_media(file_obj, text_input=None) -> IngestQueue
Input: Raw file object (audio/image) or text string.
Output: Created IngestQueue instance.
Business Rules: Saves file to disk. (Note: AI processing logic to populate predicted_action will use gemini 2.5 flash.  create .env file for the kesy to be placesd in.e; focus is on storage).
Service Function 2: process_ingest_item(ingest_id, verified_data) -> GardenEvent
Input: ingest_id (int), verified_data (dict containing confirmed plant_id, zone_id, event_type).
Output: The created GardenEvent.
Business Rules:
Validates that plant_id belongs to zone_id (if both provided).
Atomic Transaction: Creates GardenEvent, marks IngestQueue as processed=True (or deletes it, depending on retention policy—PRD implies deletion/removal from DOM, but soft delete/flag is safer for audit. We will use processed=True).
3. The Interface (Phase 3 - Views & Templates)
URL Structure:
/dashboard/ (GET)
/ingest/ (POST)
/events/create_from_ingest/<int:ingest_id>/ (POST)
View Logic:
DashboardView: Fetches IngestQueue.objects.filter(processed=False) and GardenEvent.objects.all()[:10].
IngestView: Calls ingest_media. Returns HTMX toast or partial.
ConfirmIngestView: Calls process_ingest_item. Returns HTMX (empty string or success message to remove card).
Template Strategy:
base.html: Standard HTML5 boilerplate + HTMX script.
dashboard.html: Full page render.
partials/inbox_card.html: HTMX partial for an inbox item.
partials/event_row.html: HTMX partial for the history list.
4. The Harness (Verification)
Management Command: core/management/commands/verify_garden_flow.py
Success Criteria:
Create a Zone ("Greenhouse") and Plant ("Tomato").
Simulate an ingestion via ingest_media (create IngestQueue item).
Call process_ingest_item with the Ingest ID and the Tomato/Greenhouse IDs.
Assert: IngestQueue item is processed=True.
Assert: GardenEvent count increased by 1.
Assert: GardenEvent is linked to the correct Tomato instance.
Print "Garden Flow Verification Successful".
5. Negative Context (Constraints)
Do not use Django generic Class Based Views (CreateView/UpdateView) for the "Confirm" action—use a functional view wrapping the Service layer.
Do not add a Javascript build step (Webpack/Vite). Use CDN links for HTMX.
Do not put business logic (e.g., creating the Event object) inside the views.py.
Do not use Bootstrap or Tailwind. Use simple, semantic vanilla CSS.