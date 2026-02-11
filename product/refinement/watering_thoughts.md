# Watering Logic Refinement

## Context
Current watering events are often incorrectly linked to specific plants when they should apply to an entire zone (garden bed). Users often mention plants as a way to identify the area (e.g., "watered the tomatoes"), but the intent is usually to water the whole bed.

## Proposed Logic

### 1. Default: Zone-Wide Watering
- By default, a `WATER` event should be associated with a `Zone` only (`plant_id = NULL`).
- This simplifies data entry and reflects the reality of irrigation (drip lines, sprinklers, or hose watering of a bed).

### 2. Exception: Plant-Specific Watering
- Individual plants (e.g., fruit trees, large shrubs, or specific plants in distress) may receive targeted watering.
- The UI must allow selecting a specific plant for a `WATER` event.
- AI should only link to a specific plant if the language is explicit (e.g., "gave the lemon tree a bucket of water") or if the plant is isolated/notable.

### 3. AI Enrichment Adjustments
- Update Gemini prompt to distinguish between "Area Watering" and "Targeted Watering".
- If a plant is mentioned in a watering context, the AI should:
    - Default to `plant_id = null` but set the `predicted_zone` based on where that plant is known to be.
    - Only set `plant_id` if the user implies a specific, individual action rather than a general bed maintenance.

### 4. UI/UX Refinement
- The `action_X_plant_id` dropdown should have an explicit **"Whole Zone / No Specific Plant"** option (currently it says "-- New Plant --" which is confusing for maintenance tasks).
- If "Whole Zone" is selected, the "New Plant" fields (Species/Custom Name) should be hidden and ignored.

## Multi-Zone Challenge
The user's example ("Sowed Spinach in Greenhouse, watered Tomatoes in Garden") highlights a limitation where a single ingestion item assumes a single zone.
- **Thought:** We should consider moving `zone_id` from the card-level to the action-level in the `confirm_ingest` view and the `IngestQueue.predicted_data`.
- This would allow one voice note to trigger events in multiple parts of the garden.
