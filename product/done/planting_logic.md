# Planting Logic & Traceability Refinement

## Current State: The "Instance" Model
Currently, the `Plant` model represents a **specific batch or individual instance** of a plant, not the general category (Species).

*   **Identification:** A `Plant` record (e.g., "Spinach") is created once (usually at the `SOW` or `PLANT` stage).
*   **Journey Tracking:** The journey is recorded via `GardenEvent` records linked to that specific `Plant` ID.
    *   **SOW Event:** Status -> `Seedling`
    *   **GERMINATE Event:** Status -> `Germinated`
    *   **TRANSPLANT Event:** Status -> `Planted` (Zone updates from Greenhouse to Garden)
    *   **FIRST_HARVEST Event:** Status -> `Providing`
*   **Viewing History:** To see a specific plant's journey, we currently query all `GardenEvent` records filtered by that `plant_id`, ordered by date.

### Current Limitation: The "Naming" Collision
Because the model doesn't distinguish between the **Species** (Spinach) and the **Instance** (Batch #45), users often name a plant simply "Spinach". If multiple "Spinach" batches exist simultaneously:
1.  The AI may match events to the wrong "Spinach" record.
2.  The UI dropdown may select the first "Spinach" it finds.

---

## Proposed Refinement: Species vs. Planted Instance

### 1. Conceptual Separation
We should split the model to support a cleaner hierarchy:
*   **`Vegetable` (or `Species`):** A static catalog (e.g., "Spinach", "Detroit Red Beet", "Roma Tomato"). Contains data that doesn't change per planting (e.g., typical days to maturity).
*   **`PlantedInstance` (Current `Plant` model):** A specific batch with a unique ID, linked to a `Vegetable`. (e.g., "Spinach - Batch #42").

### 2. Implementation Strategy
*   **Rename `Plant` to `PlantedInstance`** (or keep as `Plant` but add a `species` Foreign Key).
*   **Auto-Naming:** When a new "Spinach" is planted, the system could automatically name it "Spinach [Date]" or "Spinach [ShortUUID]" to prevent collisions in the AI matching logic.
*   **Filtering Suggestions:** In the Ingest UI, suggestions should be filtered by:
    *   **Zone:** If the text says "transplant from greenhouse," only suggest plants currently in the greenhouse.
    *   **Status:** Only suggest "Germinated" or "Sowed" plants for a "Transplant" action (in case we forget to track the germination date).

### 3. Visualizing the Journey
To fulfill the need for a "Journey View," we should implement a **Plant Timeline View**:
*   **Input:** `plant_id`
*   **Output:** A vertical timeline showing the transition of statuses, changes in zones, and all associated metadata (seed counts, vigor scores) over time.

---
**Status:** Ready
**Date:** 2026-01-28

# User Stories: Species vs. Planted Instance

## 1. Schema & Foundation
### User Story 13: Gardener - Species Catalog Definition
**Narrative:** As a Gardener, I want to define vegetable species in a central catalog, so that I can standardize plant types and avoid repetitive data entry.

**Acceptance Criteria (AC):**
- New `Species` model created in `core/models.py` with fields: `name` (CharField, unique), `description` (TextField, optional), and `default_days_to_maturity` (IntegerField, optional).
- `Species` inherits from `TimeStampedModel`.
- Register `Species` in `core/admin.py` for manual management.
- Initial migration created to support the new table.

**Technical Implementation Notes:**
- Create `Species` model in `core/models.py`.
- Update `core/admin.py`.

### User Story 14: Gardener - Plant Instance Linking & Auto-Naming
**Narrative:** As a Gardener, I want my planting instances to be linked to a species and automatically named with a unique identifier, so that I can distinguish between different batches of the same vegetable.

**Acceptance Criteria (AC):**
- `Plant` model updated in `core/models.py` to include a `species` Foreign Key (null=True for migration safety).
- `core/services/processing.py` updated: When a new `Plant` is created from ingestion, its name is automatically generated as `[Species Name] - [Current Date]` (e.g., "Spinach - 2026-01-28").
- If multiple plantings of the same species occur on the same day, append a suffix (e.g., "- 2").
- The AI enrichment prompt in `core/services/enrichment.py` is updated to identify "Species" from the text and map them to the `Species` ID.

**Technical Implementation Notes:**
- Update `Plant` model in `core/models.py`.
- Modify `process_ingest_item_multi` in `core/services/processing.py` to handle naming logic.
- Update system prompt in `core/services/enrichment.py` to recognize species vs instances.

## 2. Intelligence & Ingestion
### User Story 15: System - Context-Aware Plant Matching
**Narrative:** As a System, I want to filter plant suggestions in the inbox based on the zone and event type mentioned in my notes, so that the Gardener can confirm events faster with fewer errors.

**Acceptance Criteria (AC):**
- In `core/templates/core/partials/inbox_card.html`, the plant selection dropdown for `TRANSPLANT` events only shows plants whose current `zone` matches the source zone identified in the text (if a source zone is detected).
- The plant selection dropdown for `TRANSPLANT` events defaults to showing plants with status `SEEDLING`, `GERMINATED`, or `SOWED`.
- If the AI detects a "from [Zone]" in the text, that zone is used as a filter for the suggested plants list in the dropdown.

**Technical Implementation Notes:**
- Modify `inbox_card.html` template logic.
- Update `enrichment.py` to specifically extract "Source Zone" vs "Target Zone" for transplant events.

## 3. Visualization
### User Story 16: Gardener - Plant Journey Timeline View
**Narrative:** As a Gardener, I want to view a vertical timeline of a specific plant instance's history, so that I can analyze its growth performance and nursery duration.

**Acceptance Criteria (AC):**
- New functional view `plant_detail` created in `core/views.py`.
- New template `core/plant_detail.html` that renders a vertical CSS timeline of all `GardenEvent` records linked to the plant.
- Timeline displays: Date, Event Type, Zone change (if any), and Metadata (seed count, germination rate, vigor).
- A link to this view is added to each event row in the "Recent History" table on the dashboard.

**Technical Implementation Notes:**
- Add URL pattern in `core/urls.py`.
- Implement `plant_detail` view.
- Create CSS for vertical timeline in a `<style>` block within the template (keeping to vanilla CSS principles).

---
## Implementation Summary
- Stories 13, 14, 15, 16 - Complete

### File Manifest
- core/models.py
- core/admin.py
- core/services/processing.py
- core/services/enrichment.py
- core/views.py
- core/urls.py
- core/templates/core/partials/inbox_card.html
- core/templates/core/partials/event_history.html
- core/templates/core/plant_detail.html (New)
- core/migrations/0004_species_plant_species.py (New)

### Technical Debt & Risks
- **Searchability:** The species dropdown for new plants is a standard select; will need autocomplete as the catalog grows.
- **Naming Robustness:** Auto-naming relies on the presence of a species; if missing, it defaults to creating a species from the provided name.
- **AI Matching:** Extraction of `source_zone_id` for transplants is sensitive to how the user describes the move.

### Action Items
- **Refactor:** Move the auto-naming logic from the service layer into the `Plant` model's `save` method or a dedicated manager.
- **Backlog:** Add a story for 'Searchable Species Autocomplete' in the Inbox card.

### Learnings
- Ensure all new models are imported in `views.py` and `tests` to avoid `NameError` during execution.
- Carefully verify indentation when modifying multi-line test assertions to prevent collection errors.
