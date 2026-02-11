from django.urls import path
from .views import (
    DashboardView, confirm_ingest, ingest_view,
    ingest_delete,
    recipe_list, recipe_create, recipe_delete,
    event_history_partial, plant_detail
)

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('ingest/', ingest_view, name='ingest_media'),
    path('ingest/<int:ingest_id>/delete/', ingest_delete, name='ingest_delete'),
    path('events/create_from_ingest/<int:ingest_id>/', confirm_ingest, name='confirm_ingest'),
    path('events/history/', event_history_partial, name='event_history_partial'),
    path('plants/<int:plant_id>/', plant_detail, name='plant_detail'),
    
    # Recipe Book
    path('recipes/', recipe_list, name='recipe_list'),
    path('recipes/create/', recipe_create, name='recipe_create'),
    path('recipes/delete/<int:recipe_id>/', recipe_delete, name='recipe_delete'),
]
