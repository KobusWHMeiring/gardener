**Generated on:** 2026-01-28 19:59:43

### File Structure
```
.
└── .env
└── .env.example
└── config
    └── __init__.py
    └── asgi.py
    └── settings.py
    └── urls.py
    └── wsgi.py
└── core
    └── __init__.py
    └── admin.py
    └── apps.py
    └── forms.py
    └── management
        └── __init__.py
        └── commands
            └── __init__.py
    └── models.py
    └── services
        └── __init__.py
        └── enrichment.py
        └── ingestion.py
        └── processing.py
    └── templates
        └── core
            └── base.html
            └── dashboard.html
            └── partials
                └── event_history.html
                └── inbox_card.html
                └── recipe_list.html
            └── plant_detail.html
            └── recipes.html
    └── tests
        └── __init__.py
        └── test_basic.py
        └── test_e2e.py
        └── test_lifecycle.py
        └── test_multi_plant.py
    └── urls.py
    └── views.py
└── db.sqlite3
└── manage.py
└── product
    └── done
        └── backlog1.md
        └── plan.md
        └── planting_logic.md
        └── PRD-01-Zones_and_Actions.md
        └── worklog1.md
    └── project_context.md
    └── ready
    └── refinement
        └── backlog.md
        └── voice_input.md
└── prompts
    └── PM.md
    └── PO.md
    └── protocol.md
└── pytest.ini
└── requirements.txt
└── summarise.py
└── uploads
    └── uploads
        └── 2026
            └── 01
                └── test.txt
                └── test_0ilf99d.txt
                └── test_bPQRbcF.txt
                └── test_c108vke.txt
                └── test_CumUgIu.txt
                └── test_Ds5bXXg.txt
                └── test_eRTztQL.txt
                └── test_o5OMDyb.txt
                └── test_tZDMWoK.txt
```

### Summarized Key Files
#### `SUMMARY: config/settings.py`
```python
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG=(bool, False)
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')
INSTALLED_APPS = [
MIDDLEWARE = [
ROOT_URLCONF = 'config.urls'
TEMPLATES = [
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'uploads'```

#### `SUMMARY: core/models.py`
```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### `SUMMARY: core/services/enrichment.py`
```python
def def enrich_ingest_item(ingest_id):
    """Uses Gemini API to enrich the ingestion item with predicted actions and metadata."""
    # ... implementation hidden ...
```

#### `SUMMARY: core/services/ingestion.py`
```python
def def ingest_media(file_obj=None, text_input=None):
    """Ingests raw media (file) or text input into the IngestQueue."""
    # ... implementation hidden ...
```

#### `SUMMARY: core/services/processing.py`
```python
def def process_ingest_item_multi(ingest_id, verified_data):
    """Converts a queued item into multiple verified garden events.
verified_data: {
    'zone_id': ...,
    'event_date': ...,
    'actions': [
        {'event_type': ..., 'plant_id': ..., 'new_plant_name': ..., 'species_id': ..., 'metadata': ...},
        ...
    ]
}"""
    # ... implementation hidden ...

def def process_ingest_item(ingest_id, verified_data):
    """Backward compatibility for single action."""
    # ... implementation hidden ...
```

#### `SUMMARY: core/views.py`
```python
class class DashboardView(ListView):  # Renders: core/dashboard.html
    """Primary dashboard view displaying recent garden events and the inbox of unprocessed items."""
    # ... implementation hidden ...

def def ingest_view(request):  # Renders: core/partials/inbox_card.html
    """View to handle ingestion from the dashboard form.
Returns the partial for the newly created inbox card."""
    # ... implementation hidden ...

def def confirm_ingest(request, ingest_id):
    """Functional view to process an ingestion item into one or more GardenEvents.
Expects POST request from HTMX with potential multiple actions."""
    # ... implementation hidden ...

def def event_history_partial(request):  # Renders: core/partials/event_history.html
    # ... implementation hidden ...

def def plant_detail(request, plant_id):  # Renders: core/plant_detail.html
    # ... implementation hidden ...

def def recipe_list(request):  # Renders: core/partials/recipe_list.html, core/recipes.html
    # ... implementation hidden ...

def def recipe_create(request):  # Renders: core/partials/recipe_list.html
    # ... implementation hidden ...

def def recipe_delete(request, recipe_id):
    # ... implementation hidden ...
```

### Full Content of Critical Files
#### `FULL: config/urls.py`
```python

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

```

#### `FULL: core/urls.py`
```python
from django.urls import path
from .views import (
    DashboardView, confirm_ingest, ingest_view,
    recipe_list, recipe_create, recipe_delete,
    event_history_partial, plant_detail
)

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('ingest/', ingest_view, name='ingest_media'),
    path('events/create_from_ingest/<int:ingest_id>/', confirm_ingest, name='confirm_ingest'),
    path('events/history/', event_history_partial, name='event_history_partial'),
    path('plants/<int:plant_id>/', plant_detail, name='plant_detail'),
    
    # Recipe Book
    path('recipes/', recipe_list, name='recipe_list'),
    path('recipes/create/', recipe_create, name='recipe_create'),
    path('recipes/delete/<int:recipe_id>/', recipe_delete, name='recipe_delete'),
]

```

