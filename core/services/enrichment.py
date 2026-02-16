import google.genai as genai
import base64
import json
import re
from django.conf import settings
from django.utils import timezone
from core.models import IngestQueue, GardenEvent, FertilizerRecipe, Plant, Species, Zone

def enrich_ingest_item(ingest_id):
    """
    Uses Gemini API to enrich the ingestion item with predicted actions and metadata.
    """
    ingest_item = IngestQueue.objects.get(id=ingest_id)
    
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or api_key == 'your-api-key-here':
        raise ValueError("GEMINI_API_KEY not configured correctly.")

    client = genai.Client(api_key=api_key)
    model_name = 'gemini-2.0-flash'

    # Define the valid event types and fetch recipes/plants/species
    event_types = [choice[0] for choice in GardenEvent.EventType.choices]
    recipes = list(FertilizerRecipe.objects.values('id', 'name'))
    plants = list(Plant.objects.values('id', 'name', 'zone_id', 'status'))
    species = list(Species.objects.values('id', 'name'))
    zones = list(Zone.objects.values('id', 'name'))
    
    current_date = timezone.now().strftime('%Y-%m-%d')
    
    prompt = f"""
    You are an expert garden assistant. 
    
    TASK:
    1. If audio is provided: 
       a. Transcribe the audio verbatim into "transcript_raw".
       b. Clean the text: Remove filler words ("um", "uh"), greetings, and non-garden context into "transcript_clean".
    2. If only text is provided:
       a. Use the text as "transcript_raw" and "transcript_clean".
    3. Analyze the "transcript_clean" and extract structured garden actions.

    Current Date: {current_date}
    Valid Event Types: {', '.join(event_types)}
    Known Fertilizer Recipes: {json.dumps(recipes)}
    Known Plants (Instances): {json.dumps(plants)}
    Known Species: {json.dumps(species)}
    Known Zones: {json.dumps(zones)}
    
    Return a JSON object ONLY with this structure:
    {{
      "transcript_raw": "Verbatim transcription or input text",
      "transcript_clean": "Cleaned version",
      "payload": {{
        "event_date": "YYYY-MM-DD or null",
        "predicted_zone": "Default Target Zone Name",
        "actions": [
          {{
            "event_type": "UPPERCASE_TYPE",
            "plant_name": "Name",
            "plant_id": int or null,
            "species_id": int or null,
            "predicted_zone": "Specific Zone for this action or null",
            "source_zone_id": int or null,
            "metadata": {{ ... }}
          }}
        ]
      }}
    }}

    Logic Rules:
    - If the user says "Sowed Spinach", this is a NEW instance. `plant_id` is null, `species_id` is for Spinach.
    - If the user says "Transplant Spinach from Greenhouse to Garden", `plant_id` should match the existing Spinach instance in the Greenhouse. `source_zone_id` is the Greenhouse ID. `predicted_zone` is Garden.
    - RE-LOCATION RULE: If an existing `plant_id` is provided and the `predicted_zone` is different from its current zone, the `event_type` MUST be `TRANSPLANT`.
    - WATERING RULE: Default to `plant_id: null` for watering events unless a specific individual plant is clearly the sole target (e.g., "watered the lemon tree"). Mentioning a crop (e.g., "watered the tomatoes") usually means watering the whole zone/bed.
    - MULTI-ZONE: If actions happen in different zones, specify the `predicted_zone` inside EACH action.
    - Greenhouse/Tray Rule: Any activity in the "Greenhouse" or mentioned as "seedling tray" MUST use `event_type: SOW` (never `PLANT`) and `is_direct: false`.
    - FERTIGATION RULE: When watering mentions fertilizers (e.g., "watered with worm tea", "fertigated with comfrey tea", "added fertilizer to irrigation"):
        a) Add fertilizer information to the WATER event's metadata with key "fertilizer" containing the description
        b) Also create a separate FERTILIZE event for the same zone(s) with the fertilizer details in metadata
        c) Match the fertilizer description against Known Fertilizer Recipes - if a match is found, set "recipe_id" in the action
    """

    try:
        content_parts = [{'text': prompt}]
        if ingest_item.audio_file:
            # Detect mime type from extension
            ext = ingest_item.audio_file.name.split('.')[-1].lower()
            mime_type = "audio/webm"
            if ext == 'mp4' or ext == 'm4a':
                mime_type = "audio/mp4"
            elif ext == 'ogg':
                mime_type = "audio/ogg"
            elif ext == 'wav':
                mime_type = "audio/wav"

            audio_bytes = ingest_item.audio_file.read()
            # Reset file pointer after reading
            ingest_item.audio_file.seek(0)
            content_parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(audio_bytes).decode('utf-8')
                }
            })
        else:
            content_parts.append({"text": f"User Text: {ingest_item.raw_text}"})

        response = client.models.generate_content(
            model=model_name,
            contents=[{
                "role": "user",
                "parts": content_parts
            }]
        )
        response_text = getattr(response, 'output_text', None) or getattr(response, 'text', '')
        # Clean response text in case it contains markdown formatting
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data_full = json.loads(json_match.group())
        else:
            raise ValueError("Could not parse JSON from Gemini response")
            
        ingest_item.raw_text = data_full.get('transcript_raw', ingest_item.raw_text)
        ingest_item.transcript_clean = data_full.get('transcript_clean', '')
        
        data = data_full.get('payload', {})
        
        # Extract predicted date and default zone
        predicted_date = data.get('event_date')
        default_zone_name = data.get('predicted_zone')
        
        actions = data.get('actions', [])
        if not actions and data.get('event_type'):
            # Backward compatibility for single action
            actions = [{
                "event_type": data.get('event_type'),
                "plant_name": data.get('predicted_plant'),
                "metadata": data.get('metadata', {})
            }]

        for action in actions:
            action_zone_name = action.get('predicted_zone') or default_zone_name
            
            # Helper to find zone ID by name for enrichment logic
            action_zone_id = None
            if action_zone_name:
                for z in zones:
                    if z['name'].lower() == action_zone_name.lower():
                        action_zone_id = z['id']
                        break

            # Re-location Rule Enforcement: 
            # If we have a plant_id and it's moving to a different zone, it's a TRANSPLANT
            p_id = action.get('plant_id')
            if p_id:
                existing_plant = next((p for p in plants if p['id'] == p_id), None)
                if existing_plant and action_zone_id and existing_plant['status'] != Plant.Status.REMOVED:
                    if existing_plant['zone_id'] != action_zone_id:
                        if action.get('event_type') == GardenEvent.EventType.PLANT:
                            action['event_type'] = GardenEvent.EventType.TRANSPLANT
            
            # WATERING RULE: If it's a watering event and we have a plant name but not a specific plant_id,
            # or if it's a generic crop name, ensure plant_id is null to target the zone.
            if action.get('event_type') == GardenEvent.EventType.WATER:
                # If the AI predicted a plant_id but it's a common crop name, maybe nullify it?
                # Actually, the prompt now tells it to default to null. 
                # Let's just ensure if plant_id is present, we keep the action_zone_name updated.
                pass

            # Greenhouse/Tray Rules Enforcement
            is_greenhouse = (action_zone_name and 'greenhouse' in action_zone_name.lower()) or \
                            'greenhouse' in ingest_item.raw_text.lower() or \
                            'tray' in ingest_item.raw_text.lower()
            
            if is_greenhouse:
                # Rule: Greenhouse/Tray is always SOW, not PLANT
                if action.get('event_type') == GardenEvent.EventType.PLANT:
                    action['event_type'] = GardenEvent.EventType.SOW
                
                # Rule: Greenhouse/Tray is always indirect
                if action.get('event_type') == GardenEvent.EventType.SOW:
                    if 'metadata' not in action:
                        action['metadata'] = {}
                    action['metadata']['is_direct'] = False

        # FERTIGATION LOGIC: If WATER events have fertilizer metadata, create FERTILIZE events
        additional_fertilize_actions = []
        for action in actions:
            if action.get('event_type') == GardenEvent.EventType.WATER:
                metadata = action.get('metadata', {})
                fertilizer_info = metadata.get('fertilizer')
                if fertilizer_info:
                    # Create a matching FERTILIZE event for the same zone
                    fertilize_action = {
                        'event_type': GardenEvent.EventType.FERTILIZE,
                        'plant_id': action.get('plant_id'),  # Same plant (usually None for fertigation)
                        'plant_name': action.get('plant_name'),
                        'species_id': action.get('species_id'),
                        'predicted_zone': action.get('predicted_zone'),
                        'source_zone_id': action.get('source_zone_id'),
                        'metadata': {'fertilizer': fertilizer_info},
                        'recipe_id': action.get('recipe_id')  # Pass through if AI matched a recipe
                    }
                    additional_fertilize_actions.append(fertilize_action)
        
        # Append the fertilize actions to the main actions list
        actions.extend(additional_fertilize_actions)

        ingest_item.predicted_action = actions[0]['event_type'] if actions else 'NOTE'
        ingest_item.predicted_data = {
            'engine': model_name,
            'extracted_data': data,
            'predicted_date': predicted_date,
            'predicted_zone_name': default_zone_name,
            'actions': actions,
            'raw_response': response_text
        }
        ingest_item.save()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Re-raise to be handled by the view
        raise e

    return ingest_item
