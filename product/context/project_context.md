# Project Context: Garden Data Centralization

## Overview
Garden Data Centralization is a Django-based application designed to streamline the tracking of garden activities. It allows users to ingest raw information (notes, photos, etc.) into a processing queue, where AI (Gemini) predicts relevant garden events for quick verification and archival. The system tracks the full lifecycle of a plant from seed to termination, providing deep insights into garden performance.

## Design Principles
- **Logic Isolation:** All business logic resides in the `core/services/` layer. Views are thin and primarily handle request/response orchestration.
- **Minimalist Frontend:** The application uses semantic vanilla CSS and HTMX for a responsive, "Single Page App" feel without the complexity of a JavaScript build pipeline (No React/Vue/Tailwind).
- **Atomic Reliability:** State changes (e.g., moving an item from the Ingest Queue to Garden Events) are performed as atomic database transactions, including automatic status transitions.
- **Verification First:** A robust suite of automated integration tests (using `pytest`) verifies the entire system flow end-to-end, ensuring stability and data integrity during development without affecting production records.
- **AI-Augmented Workflow:** AI is used as a "suggestive" layer to reduce manual data entry. It supports fuzzy matching of existing plants/zones and extraction of complex metadata (dates, seed counts, vigor scores).

## Architecture & Implementation

### 1. Data Model (The Schema)
- **Zone:** Physical areas with metadata including `size_m2`, `irrigation_type` (Drip, Manual, Sprinkler), and `sun_hours`.
- **Species:** A central catalog of plant types (e.g., "Spinach", "Roma Tomato") with default growth parameters.
- **Plant (Instance):** Tracks specific batches or individual plants, linked to a `Species`. Implements a strict **Status Machine** (`Seedling`, `Germinated`, `Planted`, `Providing`, `Removed`).
- **FertilizerRecipe:** A library of nutrient recipes (`name`, `ingredients`, `instructions`) linked to fertilization events.
- **IngestQueue:** A staging area for raw inputs. Stores AI-extracted structured JSON including multiple predicted actions.
- **GardenEvent:** Permanent records of actions. Supports deep traceability via `parent_event` links (e.g., linking a `Transplant` back to a `Sow`) and rich metadata in a `JSONField`.

### 2. Service Layer (The Logic)
- **Ingestion Service (`ingest_media`):** Handles initial saving of raw data and triggers enrichment.
- **Enrichment Service (`enrich_ingest_item`):** Integrates with **Gemini 2.0 Flash**. Features:
    - **Multi-Action Extraction:** Can identify multiple plants/actions in a single sentence (e.g., "Planted 10 beans and 5 peas").
    - **Fuzzy Matching:** Automatically maps extracted text to known `Plant`, `Species`, and `Zone` records.
    - **Context-Aware Matching:** Suggests source zones for transplants and applies the "Greenhouse Rule" (Sowing in greenhouse is indirect).
    - **Greenhouse/Tray Rule:** Automatically enforces that any activity in the "Greenhouse" or "Seedling Tray" is recorded as a `SOW` event (instead of `PLANT`) and sets `is_direct` to `false`.
    - **Date Extraction:** Normalizes natural language dates (e.g., "26th of Jan") into structured formats.
- **Processing Service (`process_ingest_item_multi`):** Atomically creates multiple events/plants from one ingestion. It manages the plant lifecycle by updating `Plant.status` and implements **Auto-Naming** (e.g., "Spinach - 2026-01-28") to ensure unique identifiers for batches.

### 3. Interface (The UI)
- **Dashboard:** Features an **HTMX Inbox** where users can confirm or edit AI-suggested metadata (Direct/Indirect, Seed Counts, Dates) and create new plant records on the fly.
- **Plant Journey Timeline:** A dedicated view (`plant_detail`) providing a vertical CSS timeline of a specific plant's history, from sowing to termination.
- **Auto-Refreshing History:** The history table listens for HTMX triggers (`eventConfirmed`) to refresh dynamically and links each plant to its journey view.
- **Recipe Book:** A dedicated HTMX CRUD interface for managing the fertilizer library.
- **Admin Panel:** Fully customized Django admin with specialized filters and list views for all garden entities.

### 4. Verification & Tooling
- **Automated Verification:** Comprehensive tests in `core/tests/` use `pytest` and an isolated test database. 
- **Lifecycle Testing:** `core/tests/test_lifecycle.py` verifies the full "Golden Path" state transitions.
- **Frontend E2E Testing:** Uses **Playwright** (`core/tests/test_e2e.py`) to verify real browser interactions, including HTMX swaps and form submissions for multiple plants.
- **Environment Management:** Uses `django-environ` and `whitenoise` for robust configuration and static serving.

## Current Status
- **Planting Logic & Traceability Complete:** `Species` catalog, auto-naming, and the vertical timeline journey view are fully operational.
- **Robust Multi-Action Processing:** Ingestion queue handles multiple actions with resilient indexing and backend fallbacks.
- **Testing Infrastructure:** Both backend logic and frontend HTMX interactions are covered by automated tests.
- **Next Steps:** Focused on harvest weight tracking and "Ready to Transplant" notifications.
