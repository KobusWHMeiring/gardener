from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import IngestQueue, GardenEvent, Plant, Species

def process_ingest_item_multi(ingest_id, verified_data):
    """
    Converts a queued item into multiple verified garden events.
    verified_data: {
        'zone_id': ...,
        'event_date': ...,
        'actions': [
            {'event_type': ..., 'plant_id': ..., 'new_plant_name': ..., 'species_id': ..., 'metadata': ...},
            ...
        ]
    }
    """
    created_events = []
    created_plant_names = []
    with transaction.atomic():
        ingest_item = IngestQueue.objects.select_for_update().get(id=ingest_id)
        zone_id = verified_data.get('zone_id')
        event_date_str = verified_data.get('event_date')
        
        if event_date_str:
            event_date = timezone.datetime.strptime(event_date_str, '%Y-%m-%d').date()
        else:
            event_date = timezone.now().date()

        for action in verified_data.get('actions', []):
            action_zone_id = action.get('zone_id') or zone_id
            action_event_date_str = action.get('event_date') or event_date_str
            
            if action_event_date_str:
                action_event_date = timezone.datetime.strptime(action_event_date_str, '%Y-%m-%d').date()
            else:
                action_event_date = event_date # Use the parsed global date

            plant_id = action.get('plant_id')
            new_plant_name = action.get('new_plant_name')
            species_id = action.get('species_id')
            event_type = action.get('event_type')
            
            plant = None
            if plant_id:
                plant = Plant.objects.select_for_update().get(id=plant_id)
                
                # Auto-correct PLANT to TRANSPLANT if zone changes for an existing plant
                if event_type == GardenEvent.EventType.PLANT and plant.zone_id != int(action_zone_id):
                    event_type = GardenEvent.EventType.TRANSPLANT

                # Allow zone mismatch ONLY if it's a transplant (moving the plant)
                if plant.zone_id != int(action_zone_id) and event_type != GardenEvent.EventType.TRANSPLANT:
                    raise ValidationError(f"Plant {plant.name} does not belong to the selected zone.")
            elif new_plant_name:
                # Resolve species
                species = None
                if species_id:
                    species = Species.objects.get(id=species_id)
                else:
                    # Try to find species by name or create it
                    species, _ = Species.objects.get_or_create(name=new_plant_name)
                
                # Auto-naming logic: [Species Name] - [YYYY-MM-DD]
                base_name = f"{species.name} - {action_event_date.strftime('%Y-%m-%d')}"
                final_name = base_name
                counter = 1
                while Plant.objects.filter(name=final_name).exists() or final_name in created_plant_names:
                    counter += 1
                    final_name = f"{base_name} - {counter}"
                
                plant = Plant.objects.create(
                    name=final_name,
                    species=species,
                    zone_id=action_zone_id,
                    status=Plant.Status.SEEDLING
                )
                created_plant_names.append(final_name)

            event_kwargs = {
                'plant': plant,
                'zone_id': action_zone_id,
                'event_type': event_type,
                'metadata': action.get('metadata', {}),
            }
            if action_event_date_str:
                event_kwargs['performed_at'] = action_event_date_str

            event = GardenEvent.objects.create(**event_kwargs)
            created_events.append(event)

            # Update status and potentially zone
            if plant:
                status_map = {
                    GardenEvent.EventType.SOW: Plant.Status.SEEDLING,
                    GardenEvent.EventType.GERMINATE: Plant.Status.GERMINATED,
                    GardenEvent.EventType.PLANT: Plant.Status.PLANTED,
                    GardenEvent.EventType.TRANSPLANT: Plant.Status.PLANTED,
                    GardenEvent.EventType.FIRST_HARVEST: Plant.Status.PROVIDING,
                    GardenEvent.EventType.TERMINATE: Plant.Status.REMOVED,
                }
                if event_type in status_map:
                    plant.status = status_map[event_type]
                
                # If transplanting, move the plant to the new zone
                if event_type == GardenEvent.EventType.TRANSPLANT:
                    plant.zone_id = action_zone_id
                
                plant.save()

        ingest_item.processed = True
        ingest_item.save()
    return created_events

def process_ingest_item(ingest_id, verified_data):
    """
    Backward compatibility for single action.
    """
    # Wrap the single action into the multi-action format
    multi_data = {
        'zone_id': verified_data.get('zone_id'),
        'event_date': verified_data.get('event_date'),
        'actions': [{
            'event_type': verified_data.get('event_type'),
            'plant_id': verified_data.get('plant_id'),
            'new_plant_name': verified_data.get('new_plant_name'),
            'metadata': verified_data.get('metadata', {})
        }]
    }
    events = process_ingest_item_multi(ingest_id, multi_data)
    return events[0] if events else None