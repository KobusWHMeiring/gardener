from django.db.models import Avg, F, ExpressionWrapper, fields
from django.db.models.functions import ExtractDay
from core.models import Zone, GardenEvent
from datetime import timedelta

def calculate_watering_frequency(zone_id):
    """
    Calculates the average watering frequency for plants within a given zone.
    Returns the average days between watering events, or None if no watering events are found.
    """
    watering_events = GardenEvent.objects.filter(
        zone_id=zone_id,
        event_type=GardenEvent.EventType.WATER
    ).order_by('performed_at')

    if not watering_events.exists():
        return None

    # Calculate differences between consecutive watering events for each plant
    # This approach is simplified and averages across all watering events in the zone,
    # not strictly per-plant then averaged. For a more precise per-plant average,
    # a more complex query or Python-side processing would be needed.
    
    # Get all watering event dates for the zone
    event_dates = list(watering_events.values_list('performed_at', flat=True))

    if len(event_dates) < 2:
        return None # Need at least two events to calculate a frequency

    # Calculate the average difference between consecutive events
    total_diff_days = 0
    count = 0
    for i in range(1, len(event_dates)):
        diff = event_dates[i] - event_dates[i-1]
        total_diff_days += diff.days
        count += 1
    
    if count > 0:
        return total_diff_days / count
    else:
        return None
