# Project Backlog: Garden Data Centralization

## Phase 0: Project Initiation

- [x] **US0.1: Project Scaffolding**
  **As a developer**, I want to initialize the Django project structure and the core application so that I have a clean foundation for development.
  **Acceptance Criteria:**
  - Django project `config` initialized in the root directory.
  - `core` app created and registered in `INSTALLED_APPS`.
  - `manage.py` is functional.
  
- [x] **US0.2: Dependency & Environment Setup**
  **As a developer**, I want to configure the whitelisted libraries and environment variables so that the project follows the established protocol.
  **Acceptance Criteria:**
  - `requirements.txt` created with `django-environ`, `django-extensions`, `whitenoise`, and `pytest-django`.
  - `.env` file created (templated from `.env.example`).
  - `config/settings.py` updated to use `environ` for `SECRET_KEY` and `DEBUG`.

- [x] **US0.3: Static & Media Configuration**
  **As a developer**, I want to configure Whitenoise and media storage so that files are served correctly and ingestion works.
  **Acceptance Criteria:**
  - `whitenoise` middleware added to `settings.py`.
  - `STATIC_ROOT` and `MEDIA_ROOT` defined.
  - `MEDIA_URL` configured to point to `uploads/` as per the plan.

## Phase 1: Foundation (The Schema)

- [x] **US1: Core Model Definitions**
  **As a developer**, I want to define the fundamental data structures (Zone, Plant, GardenEvent, IngestQueue) so that I can reliably store and relate garden information.
  **Acceptance Criteria:**
  - `TimeStampedModel` abstract base class implemented with `created_at` and `updated_at`.
  - `Zone` model with `name` and `sunlight_level` (Full Sun, Partial, Shade).
  - `Plant` model with `name`, `zone` (FK), and `status` (Seedling, Vegetative, Flowering, Harvested, Dead).
  - `IngestQueue` model to store raw files, text, and predicted AI data with a `processed` flag.
  - `GardenEvent` model to track activities (`Water`, `Plant`, `Seed`, `Note`, `Harvest`, `Fertilize`).
  **Test Cases:**
  - Verify that saving any model automatically populates `created_at`.
  - Verify that a `GardenEvent` can be created for a `Zone` without requiring a specific `Plant`.
  - Verify `IngestQueue` defaults `processed` to `False`.

## Phase 2: Logic (The Services)

- [x] **US2: Media Ingestion Service**
  **As a user**, I want to submit raw text or files so that they are stored in a queue for later review.
  **Acceptance Criteria:**
  - `ingest_media(file_obj, text_input)` service function created in `core/services/`.
  - Function creates an `IngestQueue` instance and saves files to `uploads/%Y/%m/`.
  - Business logic is isolated from the view layer.
  **Test Cases:**
  - Call `ingest_media` with a dummy file; verify the file exists on disk and an `IngestQueue` record is created.
  - Call `ingest_media` with a text string; verify `raw_text` is correctly saved.

- [x] **US3: Ingest Processing Logic**
  **As a user**, I want to convert a queued item into a verified garden event so my records stay updated.
  **Acceptance Criteria:**
  - `process_ingest_item(ingest_id, verified_data)` service function created.
  - Validates that the selected `Plant` belongs to the specified `Zone`.
  - Atomic operation: Creates a `GardenEvent` and sets `IngestQueue.processed = True`.
  **Test Cases:**
  - Successfully process an item and verify the `GardenEvent` matches the `verified_data`.
  - Verify that if the event creation fails, the `IngestQueue` item remains `processed=False` (rollback).

## Phase 3: Interface (Views & Templates)

- [x] **US4: Dashboard UI & HTMX Integration**
  **As a user**, I want a central dashboard to see my pending tasks and recent garden history.
  **Acceptance Criteria:**
  - `/dashboard/` view implemented using `DashboardView`.
  - Dashboard displays a list of unprocessed `IngestQueue` items as "Inbox Cards".
  - Dashboard displays a "History" table with the 10 most recent `GardenEvent` entries.
  - `base.html` includes HTMX via CDN.
  **Test Cases:**
  - Load the dashboard and ensure pending items appear in the inbox section.
  - Ensure recent events appear in the history section.

- [x] **US5: Event Confirmation Workflow**
  **As a user**, I want to click a button on an inbox card to instantly create an event and see the card disappear.
  **Acceptance Criteria:**
  - `/events/create_from_ingest/<int:ingest_id>/` functional view implemented.
  - Returns an HTMX response that removes the card from the DOM upon success.
  - No Django generic Class Based Views used for the confirmation action.
  - Styling uses simple, vanilla CSS.
  **Test Cases:**
  - Trigger the confirmation via a POST request; verify the `IngestQueue` item is marked processed.
  - Verify the HTMX response leads to the removal of the specific inbox card element.

## Phase 4: Verification (The Harness)

- [x] **US6: System Flow Verification Command**
  **As a developer**, I want a management command to verify the entire system flow from ingestion to event creation.
  **Acceptance Criteria:**
  - `python manage.py verify_garden_flow` command implemented.
  - Command creates test data, simulates ingestion, simulates processing, and asserts results.
  **Test Cases:**
  - Run the command in a clean environment and verify it prints "Garden Flow Verification Successful".

## Phase 5: AI Enrichment & Ingestion UI

- [x] **US7: Dashboard Ingestion Form**
  **As a user**, I want to submit notes or upload photos directly from the dashboard so I can quickly record garden activity.
  **Acceptance Criteria:**
  - Ingestion form added to `dashboard.html`.
  - Supports text input and file upload.
  - Submits via HTMX to `/ingest/`.
  - On success, the new card appears in the Inbox without a page refresh.

- [x] **US8: AI Prediction Service**
  **As a user**, I want the system to automatically suggest the event type and plant from my raw input so I can confirm records faster.
  **Acceptance Criteria:**
  - `enrich_ingest_item(ingest_id)` service created.
  - Integrates with Gemini (via a mock or stub for now, or real API if keys provided).
  - Populates `predicted_action` and `predicted_data`.
  - Triggered automatically after `ingest_media`.
