# Product Requirements Document (PRD) Draft: Garden Specific Screen

## Problem Statement
Users currently lack a consolidated view of information pertaining to a specific garden (zone). While individual plant details are available, there's no central place to understand the overall health, activity, and key metrics for a designated garden area. This makes it difficult for users to assess garden performance, plan interventions, or optimize resources (like water or nutrients) at a garden-level granularity.

## Strategic Goal
To provide users with a comprehensive, at-a-glance overview of individual garden zones, enabling better decision-making, proactive management, and improved overall garden productivity and health. This feature aims to enhance the analytical capabilities of the system beyond individual plant tracking, moving towards zone-level insights.

## Proposed Scope

### In Scope:
*   **Garden Overview Page:** A dedicated page accessible via a new navigation entry (e.g., "Gardens" or "Zones").
*   **Garden Selection:** Ability to select a specific garden (zone) to view its details. Initially, this could be a simple dropdown or list of existing zones.
*   **Key Metrics Display:**
    *   **Plants in Garden:** A list or count of all plants currently assigned to the selected garden, potentially with links to their individual `plant_detail` pages.
    *   **Drip Irrigation Status:** An overview of the irrigation type for the zone and potentially a summary of recent watering events (e.g., "Last watered: 2 days ago").
    *   **Sun Hours:** Display the recorded sun hours for the zone.
    *   **Watering Frequency:** A summary or average frequency of watering events for the plants within this zone.
    *   **Recent Actions:** A concise list of the most recent `GardenEvent`s that have occurred in this specific garden, similar to the dashboard history but filtered by zone.
*   **Editable Garden Properties:** Ability to edit `zone` properties (e.g., changing `irrigation_type`, `sun_hours`) directly from this page.
*   **Basic UI/UX:** Adherence to existing minimalist frontend principles (HTMX, vanilla CSS) for rendering the data.

### Out of Scope (for initial iteration):

*   **Advanced Analytics/Charts:** Visualizations like historical watering trends, yield predictions per garden, or resource consumption graphs.
*   **Direct Action Triggers:** Buttons or forms on this page to initiate new events (e.g., "Water this garden now").
*   **Multi-Garden Comparison:** Features to compare metrics across different garden zones.
*   **Real-time Data Feeds:** Integration with external sensors for live data (e.g., soil moisture).

## UX/UI Concept
The garden-specific screen will follow the existing application's clean, minimalist design. Upon navigating to the "Gardens" section, users will be presented with a list or selection mechanism for their defined zones. Once a zone is selected, the page will dynamically load its detailed overview.

The layout will be card-based or grid-based to present key information clearly:
1.  **Header:** Garden Name and perhaps a small summary (e.g., "Main Vegetable Patch").
2.  **Plants Card:** A card listing all plants, possibly with their current status and a link to their `plant_detail` page.
3.  **Environment Card:** Details on `irrigation_type` and `sun_hours`.
4.  **Activity Card:** A condensed, chronological list of recent `GardenEvent`s for this zone, showing event type and date/time.

The page will leverage HTMX for dynamic content updates if filtering or selection mechanisms are introduced, ensuring a responsive feel without complex JavaScript. Styling will match the existing `var(--primary-color)` and other semantic CSS.

## Risks
*   **Performance:** Displaying a large number of plants or events for a single garden could impact page load times, especially with complex queries.
*   **Data Aggregation Complexity:** Calculating metrics like "watering frequency" might require more complex database queries or pre-aggregation, potentially affecting the "thin views" principle if not carefully designed within the services layer.
*   **User Confusion:** If navigation to this new page isn't intuitive or its purpose isn't clear, users might not discover or utilize it effectively.
*   **Future Feature Creep:** The overview nature of the page could quickly lead to requests for more advanced analytics or interactive features, requiring careful scope management.

Which of these approaches do you prefer, and do you have edits for the PRD scope?


# User Stories for Garden Specific Screen

## User Story [GSS-1]: View Garden Overview

**Narrative:** As a Gardener, I want to see a consolidated overview of a specific garden zone, so that I can quickly assess its health, activity, and key environmental factors.

**Acceptance Criteria (AC):**
*   The system shall provide a new navigation link (e.g., "Gardens") that leads to a list/selection of available garden zones.
*   Upon selecting a garden zone, the system shall display a dedicated page for that zone.
*   The page shall clearly display the selected Garden Zone's name.
*   The page shall list all plants currently associated with the selected garden zone, with each plant name being a clickable link to its `plant_detail` page.
*   The page shall display the `irrigation_type` for the selected garden zone.
*   The page shall display the `sun_hours` for the selected garden zone.
*   The page shall display a calculated average/summary of watering frequency for plants within the selected zone.
*   The page shall display a list of recent `GardenEvent`s filtered by the selected garden zone, similar to the dashboard history.
*   The page shall maintain the existing minimalist UI/UX design and use HTMX for any dynamic content loading.

**Technical Implementation Notes:**
*   **Models:** No new models required. `core/models.py` already defines `Zone`, `Plant`, and `GardenEvent`.
*   **URLs:**
    *   Add a new URL pattern in `config/urls.py` (e.g., `path('gardens/', include('core.garden_urls'))`) to route garden-related URLs.
    *   Create a new `core/garden_urls.py` file.
    *   Add a URL pattern in `core/garden_urls.py` for the garden list/selection (e.g., `path('', GardenListView.as_view(), name='garden_list')`).
    *   Add a URL pattern in `core/garden_urls.py` for the garden detail view (e.g., `path('<int:zone_id>/', GardenDetailView.as_view(), name='garden_detail')`).
*   **Views:**
    *   Create a `GardenListView` (e.g., `core/views.py` or `core/garden_views.py`) to list available zones.
    *   Create a `GardenDetailView` (e.g., `core/views.py` or `core/garden_views.py`) to display the details of a specific zone. This view will need to:
        *   Retrieve the `Zone` object based on `zone_id`.
        *   Query `Plant` objects filtered by the `Zone`.
        *   Query `GardenEvent` objects filtered by the `Zone`.
        *   Calculate watering frequency (requires querying `GardenEvent`s of type 'WATER' or similar, then averaging/summarizing). This logic should reside in `core/services/analytics.py` (new service).
*   **Services:**
    *   Create a new service file `core/services/analytics.py`.
    *   Implement a function in `core/services/analytics.py` to calculate watering frequency for a given zone. This will involve analyzing `GardenEvent` data.
*   **Templates:**
    *   Create `core/templates/core/garden_list.html` for listing zones.
    *   Create `core/templates/core/garden_detail.html` to display the garden-specific overview. This template will render the zone name, list of plants, irrigation type, sun hours, watering frequency, and recent events.
    *   Consider creating a partial template (e.g., `core/templates/core/partials/garden_event_history.html`) for the recent events to leverage HTMX for dynamic updates if needed.

## User Story [GSS-2]: Edit Zone Properties

**Narrative:** As a Gardener, I want to be able to edit the properties of a garden zone directly from its overview page, so that I can keep my garden information accurate and up-to-date.

**Acceptance Criteria (AC):**
*   On the Garden Detail page, there shall be an intuitive way to initiate editing of zone properties (e.g., an "Edit" button or inline editable fields).
*   The system shall allow editing of `zone` properties such as `size_m2`, `irrigation_type`, and `sun_hours`.
*   Upon successful submission, the updated zone properties shall be reflected on the page.
*   The system shall provide appropriate feedback for successful updates or validation errors.
*   The editing functionality shall leverage HTMX for a seamless, page-reload-free experience.

**Technical Implementation Notes:**
*   **Models:** No new models required. `core/models.py` defines `Zone`.
*   **Forms:**
    *   Create a new Django form `core/forms.py` (e.g., `ZoneUpdateForm`) specifically for updating `Zone` model fields.
*   **Views:**
    *   Modify `GardenDetailView` to handle POST requests for updating `Zone` properties.
    *   The view should instantiate `ZoneUpdateForm` with the `Zone` instance and `request.POST` data.
    *   Upon successful form validation and saving, it should re-render the relevant part of the `garden_detail.html` template (using HTMX).
*   **Templates:**
    *   Modify `core/templates/core/garden_detail.html` to include form elements (e.g., input fields for `size_m2`, `irrigation_type`, `sun_hours`) for editing `Zone` properties.
    *   These form elements should be configured to work with HTMX (e.g., `hx-post`, `hx-target`, `hx-swap`).
    *   Implement appropriate styling for editable fields and feedback messages.
