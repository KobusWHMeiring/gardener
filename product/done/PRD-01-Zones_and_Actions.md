# PRD-01: Garden Zones & Detailed Actions

**Status:** Complete
**Author:** AI PM / PO
**Date:** 2026-01-28

## 1. Problem Statement
The current system acts as a basic logger but lacks the depth to answer critical gardening questions regarding lifecycle efficiency and input optimization.
1.  **Zone Fidelity:** Zones need specific attributes (size, irrigation, sunlight) to normalize performance data.
2.  **Traceability Gap:** We cannot currently calculate "nursery duration" (Sow -> Transplant), "germination success", or "time to yield" (Transplant -> First Harvest).
3.  **Input Cataloging:** Fertilization is logged as text, preventing analysis of specific recipe effectiveness.
4.  **Action Nuance:** Critical variables like "Application Time" and "Vigor Observations" are missing.

## 2. Strategic Goal
Transform the system into a "Garden Optimization Engine."
*   **Traceability:** Hard-link the lifecycle of a plant from Seeding to Germination to Transplanting to First Harvest and finally Removal.
*   **Knowledge Base:** Build a library of Fertilizer Recipes to track the circular economy.
*   **Optimization:** Identify success rates (germination) and earliest windows for seeding/transplanting.

## 3. Proposed Scope

### In Scope
1.  **Zone & Recipe Management:**
    *   **Zones:** Pre-populated list with metadata (`size_m2`, `irrigation_setup`, `sun_hours`).
    *   **Fertilizer Recipes:** A new entity to store `name`, `ingredients`, and `instructions`. (Inherits `TimeStampedModel`).
2.  **Extended Lifecycle Event Tracking:**
    *   **Sow (Seeding):** Track method (Direct vs. Tray) and `seed_count`. Status: `Seedling`.
    *   **Germinate:** Track `germination_count`. Status: `Germinated`.
    *   **Transplant:** Link to a `Sow` event. Supports multiple transplants from one tray. Status: `Planted`.
    *   **First Harvest:** Milestone marking the start of production. Status: `Providing`.
    *   **Terminate/Remove:** End of lifecycle. Status: `Removed`.
3.  **Detailed Action Metadata:**
    *   **Watering:** Duration, Method.
    *   **Fertilizing:** Linked `Recipe`, `Method` (Foliar/Soil), and `Time` (Morning/Evening).
    *   **Health Check:** `vigor_score` (1-10), `vigor_observations` (text), and `observation_time`.

### Out of Scope (Phase 1)
*   Harvest weight/volume tracking.
*   Automatic alerts for "Ready to Transplant."

## 4. UX/UI Concept (HTMX-Driven)

### A. The "Recipe Book"
*   HTMX-powered CRUD interface for Fertilizer Recipes.

### B. Traceability & Status Automation
*   **Event: Sow** -> Plant Status: `Seedling`.
*   **Event: Germinate** -> Plant Status: `Germinated`.
*   **Event: Transplant** -> Plant Status: `Planted`.
*   **Event: First Harvest** -> Plant Status: `Providing`.
*   **Event: Terminate** -> Plant Status: `Removed`.

### C. Action Form Updates
*   **Fertilize Form:** Dropdown for Recipes, Method selection, Time of Day.
*   **Health Check Form:** Vigor Slider, Text Area for Observations, Time of Day.

## 5. Technical Implications & Schema Updates

### Database (`core.models`)
1.  **`FertilizerRecipe` Model:** `name`, `content`, inherits `TimeStampedModel`.
2.  **`Zone` Model Updates:** Add `size_m2`, `irrigation_type`, `sun_hours` (all `null=True` for migration safety).
3.  **`Plant` Model Updates:** Add `status` (Choices: `Seedling`, `Germinated`, `Planted`, `Providing`, `Removed`).
4.  **`GardenEvent` Model:**
    *   Add `Germinate`, `FirstHarvest`, `Terminate` to `event_type`.
    *   **Self-Referencing Link:** `parent_event` (FK to `self`) to link `Germinate`/`Transplant` back to `Sow`.
    *   **Metadata (JSONField or Columns):**
        *   `Sow`: `is_direct`, `seed_count`.
        *   `Germinate`: `germination_count`.
        *   `Water`: `duration`, `method`.
        *   `Fertilize`: `recipe_id`, `method`, `time`.
        *   `HealthCheck`: `vigor_score`, `observations`, `observation_time`.

### Services & AI Enrichment
1.  **Enrichment Service (`enrichment.py`):** Update system prompt to recognize new metadata fields and Fertilizer Recipes.
2.  **Processing Service (`processing.py`):** Logic to update `Plant.status` atomically when events are verified.

## 6. Risks & Mitigations
*   **Link Complexity:** If a `Sow` event is missing, allow "Unlinked" as fallback for transplants.
*   **One-to-Many Mapping:** Ensure a `Sow` event remains "active" as a parent for multiple `Transplant` events.

## 7. Verification Requirement
*   **System Harness:** Update `verify_garden_flow.py` to test the full lifecycle: `Sow` -> `Germinate` -> `Transplant` -> `Providing` -> `Removed`.

---
**Final Approval:** Updated 2026-01-28 per PO feedback.
**Note:** Staying on SQLite for current phase; ensure JSON compatibility.

# User Stories: PRD-01 Garden Zones & Detailed Actions

## 1. Zone & Infrastructure Management
### US-01: Enhanced Zone Metadata
**As a** gardener,  
**I want to** record specific dimensions, irrigation methods, and sunlight exposure for my garden zones,  
**so that** I can analyze plant performance against environmental conditions and normalize yield data.

**Acceptance Criteria:**
- `Zone` model updated with `size_m2` (Decimal), `irrigation_type` (Choices), and `sun_hours` (Decimal).
- Existing zones can be updated with this metadata via the admin or a future settings interface.
- Metadata fields are optional (`null=True`) to maintain compatibility with existing records.

### US-02: Fertilizer Recipe Book
**As a** gardener,  
**I want to** maintain a library of fertilizer recipes (ingredients and instructions),  
**so that** I can consistently apply and track specific nutrient inputs across my garden.

**Acceptance Criteria:**
- New `FertilizerRecipe` model created with `name`, `ingredients`, and `instructions`.
- Inherits from `TimeStampedModel`.
- Basic HTMX-powered CRUD interface for managing recipes.

## 2. Plant Lifecycle & Traceability
### US-03: Sowing & Seedling Tracking
**As a** gardener,  
**I want to** log "Sow" events specifying the method (Direct vs. Tray) and seed count,  
**so that** I can track the start of a plant's lifecycle and its initial vigor.

**Acceptance Criteria:**
- `GardenEvent` supports `SOW` event type.
- Metadata includes `is_direct` (Boolean) and `seed_count` (Integer).
- Creating/verifying a `Sow` event automatically updates the `Plant.status` to `Seedling`.

### US-04: Germination Success Logging
**As a** gardener,  
**I want to** record germination counts linked to specific sowing events,  
**so that** I can calculate germination success rates for different seed batches.

**Acceptance Criteria:**
- `GardenEvent` supports `GERMINATE` event type.
- Includes `parent_event` link to the original `SOW` event.
- Metadata includes `germination_count` (Integer).
- Verification updates `Plant.status` to `Germinated`.

### US-05: Transplanting & Nursery Duration
**As a** gardener,  
**I want to** log transplanting events that link back to the plant's origin (Sow/Germinate),  
**so that** I can measure how long plants stay in the nursery phase.

**Acceptance Criteria:**
- `GardenEvent` supports `TRANSPLANT` event type.
- Includes `parent_event` link to `SOW` or `GERMINATE` event.
- Verification updates `Plant.status` to `Planted`.
- Supports multiple transplants from a single sowing event (e.g., tray to larger pot, then to ground).

### US-06: Production & Retirement
**As a** gardener,  
**I want to** mark the start of harvest and the eventual removal of a plant,  
**so that** I can track the productive window and clean up my active plant list.

**Acceptance Criteria:**
- `GardenEvent` supports `FIRST_HARVEST` and `TERMINATE` event types.
- `FIRST_HARVEST` verification updates `Plant.status` to `Providing`.
- `TERMINATE` verification updates `Plant.status` to `Removed`.

## 3. Detailed Activity Logging
### US-07: Precision Irrigation Logging
**As a** gardener,  
**I want to** record the duration and method of watering events,  
**so that** I can optimize my water usage and identify trends in plant thirst.

**Acceptance Criteria:**
- `Water` event metadata expanded to include `duration_minutes` and `method` (e.g., Drip, Manual, Sprinkler).

### US-08: Nutritional Input Tracking
**As a** gardener,  
**I want to** link fertilization events to specific recipes and application times,  
**so that** I can evaluate the effectiveness of different nutrient recipes.

**Acceptance Criteria:**
- `Fertilize` event metadata includes `recipe_id` (FK to `FertilizerRecipe`), `application_method` (Foliar vs. Soil), and `time_of_day`.

### US-09: Plant Health Observations (Vigor)
**As a** gardener,  
**I want to** perform health checks with a numerical vigor score and qualitative notes,  
**so that** I can catch pest or disease issues early and track recovery.

**Acceptance Criteria:**
- `GardenEvent` supports `HEALTH_CHECK` event type.
- Metadata includes `vigor_score` (1-10 slider), `observations` (Text), and `observation_time`.

## 4. AI & System Intelligence
### US-10: AI Enrichment for Extended Schema
**As a** gardener,  
**I want to** use the Gemini API to automatically extract new metadata (like seed counts or vigor scores) from my raw notes,  
**so that** I can log complex data through simple text or voice-to-text input.

**Acceptance Criteria:**
- `enrichment.py` system prompt updated to recognize and structure new event types and metadata fields.
- AI correctly identifies `FertilizerRecipe` names if they exist in the DB.

### US-11: Atomic Status Transitions
**As a** system,  
**I want to** ensure that a plant's status always reflects its most recent verified event,  
**so that** my dashboard and reports are always accurate.

**Acceptance Criteria:**
- `processing.py` implements a state machine logic to update `Plant.status` during event verification.
- Transitions are performed within a database transaction.

## 5. Developer Experience & Quality
### US-12: Full Lifecycle Verification Harness
**As a** developer,  
**I want to** run a single command that tests the entire "Seed to Removal" flow,  
**so that** I can confidently refactor the system without breaking core traceability.

**Acceptance Criteria:**
- `verify_garden_flow.py` updated to include a "Golden Path" test: `Sow` -> `Germinate` -> `Transplant` -> `First Harvest` -> `Terminate`.
- Asserts correct `Plant.status` at each stage.

# Implementation Summary
- **US-01 to US-12 - Complete**
- All user stories implemented, including models, services, UI, and verification harness.

### File Manifest
- `core/models.py`: Updated `Zone`, `Plant`, and `GardenEvent` models; added `FertilizerRecipe`.
- `core/services/processing.py`: Added atomic status transitions and handling for `parent_event` and `recipe`.
- `core/services/enrichment.py`: Enhanced AI prompt for structured JSON metadata extraction.
- `core/management/commands/verify_garden_flow.py`: Updated to test the full "Seed to Removal" lifecycle.
- `core/forms.py`: Created for `FertilizerRecipe` management.
- `core/views.py`: Added recipe CRUD views and expanded dashboard context.
- `core/urls.py`: Added routes for recipe management.
- `core/templates/core/base.html`: Added navigation bar.
- `core/templates/core/recipes.html`: New template for recipe management.
- `core/templates/core/partials/recipe_list.html`: New partial for HTMX recipe list.
- `core/templates/core/partials/inbox_card.html`: Updated to support new event types and fields.

### Technical Debt & Risks
- **Metadata Parsing:** The `confirm_ingest` view currently passes `metadata` directly from POST. In a production app, this should be better validated/sanitized.
- **AI Matching:** AI matching for plants and zones by name in `inbox_card.html` is currently a simple case-insensitive substring check. This could be improved with better fuzzy matching or AI-predicted IDs.
- **Status Machine:** The status transitions are hardcoded in `processing.py`. For a more complex system, a formal State Machine library might be better.

### Learnings
- **JSON Compatibility:** SQLite handles the `JSONField` well, which is great for the flexible metadata requirements of different event types.
- **HTMX Efficiency:** Using HTMX for the "Recipe Book" allowed for a very fast implementation of CRUD without full page reloads, adhering to the project's design principles.
