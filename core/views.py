from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.http import HttpResponse
from core.models import IngestQueue, GardenEvent, Plant, Zone, FertilizerRecipe, Species
from core.services.processing import process_ingest_item
from core.services.ingestion import ingest_media
from core.forms import FertilizerRecipeForm, ZoneUpdateForm
from core.services.analytics import calculate_watering_frequency

class DashboardView(ListView):
    """
    Primary dashboard view displaying recent garden events and the inbox of unprocessed items.
    """
    template_name = 'core/dashboard.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        return GardenEvent.objects.all().order_by('-performed_at')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ingest_items'] = IngestQueue.objects.filter(processed=False).order_by('-created_at')
        context['zones'] = Zone.objects.all()
        context['plants'] = Plant.objects.all()
        context['species'] = Species.objects.all()
        context['recipes'] = FertilizerRecipe.objects.all()
        context['event_types'] = GardenEvent.EventType.choices
        context['potential_parents'] = GardenEvent.objects.filter(event_type__in=['SOW', 'GERMINATE']).order_by('-performed_at')[:20]
        return context

def ingest_view(request):
    """
    View to handle ingestion from the dashboard form.
    Returns the partial for the newly created inbox card.
    """
    if request.method == 'POST':
        file_obj = request.FILES.get('source_file')
        audio_file = request.FILES.get('audio_file')
        text_input = request.POST.get('text_input')
        
        ingest_item = ingest_media(file_obj=file_obj, text_input=text_input, audio_file=audio_file)
        
        if ingest_item:
            context = {
                'item': ingest_item,
                'zones': Zone.objects.all(),
                'plants': Plant.objects.all(),
                'species': Species.objects.all(),
                'event_types': GardenEvent.EventType.choices
            }
            return render(request, 'core/partials/inbox_card.html', context)
    
    return HttpResponse(status=400)

def ingest_delete(request, ingest_id):
    """Delete a pending ingest queue item via HTMX."""
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    ingest_item = get_object_or_404(IngestQueue, id=ingest_id)

    if ingest_item.processed:
        context = {
            'item': ingest_item,
            'zones': Zone.objects.all(),
            'plants': Plant.objects.all(),
            'species': Species.objects.all(),
            'event_types': GardenEvent.EventType.choices,
            'error_message': 'This item has already been processed and cannot be deleted.',
        }
        return render(request, 'core/partials/inbox_card.html', context, status=400)

    ingest_item.delete()
    response = HttpResponse("")
    response['HX-Trigger'] = 'ingestItemDeleted'
    return response

def confirm_ingest(request, ingest_id):
    """
    Functional view to process an ingestion item into one or more GardenEvents.
    Expects POST request from HTMX with potential multiple actions.
    """
    if request.method == 'POST':
        zone_id = request.POST.get('zone_id')
        event_date = request.POST.get('event_date') or None
        
        # Parse multiple actions using indices
        actions_data = []
        processed_indices = set()
        
        # Identify all unique action indices in the POST data
        for key in request.POST:
            if key.startswith('action_') and key.endswith('_event_type'):
                try:
                    idx = key.split('_')[1]
                    if idx in processed_indices: continue
                    processed_indices.add(idx)
                    
                    # Extract metadata for this specific action index
                    metadata = {}
                    meta_prefix = f'action_{idx}_meta_'
                    for p_key, p_val in request.POST.items():
                        if p_key.startswith(meta_prefix):
                            clean_key = p_key.replace(meta_prefix, '')
                            if p_val == 'True': metadata[clean_key] = True
                            elif p_val == 'False': metadata[clean_key] = False
                            elif p_val.isdigit(): metadata[clean_key] = int(p_val)
                            else: metadata[clean_key] = p_val

                    actions_data.append({
                        'event_type': request.POST.get(f'action_{idx}_event_type') or 'NOTE',
                        'zone_id': request.POST.get(f'action_{idx}_zone_id') or zone_id,
                        'plant_id': (lambda p: None if p == 'none' else p)(request.POST.get(f'action_{idx}_plant_id')),
                        'species_id': request.POST.get(f'action_{idx}_species_id') or None,
                        'new_plant_name': request.POST.get(f'action_{idx}_new_plant_name') or None,
                        'recipe_id': request.POST.get(f'action_{idx}_recipe_id') or None,
                        'metadata': metadata
                    })
                except (IndexError, ValueError):
                    continue

        try:
            from core.services.processing import process_ingest_item_multi
            process_ingest_item_multi(ingest_id, {
                'zone_id': zone_id,
                'event_date': event_date,
                'actions': actions_data
            })
            
            # Return empty response with trigger to refresh history
            response = HttpResponse("")
            response['HX-Trigger'] = 'eventConfirmed'
            return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f'<div class="error">Error: {str(e)}</div>', status=400)
    
    return HttpResponse("Method not allowed", status=405)

def event_history_partial(request):
    events = GardenEvent.objects.all().order_by('-performed_at')[:10]
    return render(request, 'core/partials/event_history.html', {'events': events})

def plant_detail(request, plant_id):
    plant = get_object_or_404(Plant, id=plant_id)
    events = plant.events.all().order_by('performed_at')
    return render(request, 'core/plant_detail.html', {
        'plant': plant,
        'events': events
    })

# --- Fertilizer Recipe Views ---

def recipe_list(request):
    recipes = FertilizerRecipe.objects.all().order_by('-created_at')
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/recipe_list.html', {'recipes': recipes})
    return render(request, 'core/recipes.html', {'recipes': recipes, 'form': FertilizerRecipeForm()})

def recipe_create(request):
    if request.method == 'POST':
        form = FertilizerRecipeForm(request.POST)
        if form.is_valid():
            form.save()
            recipes = FertilizerRecipe.objects.all().order_by('-created_at')
            return render(request, 'core/partials/recipe_list.html', {'recipes': recipes})
    return HttpResponse("Method not allowed", status=405)

def recipe_delete(request, recipe_id):
    if request.method == 'DELETE':
        recipe = get_object_or_404(FertilizerRecipe, id=recipe_id)
        recipe.delete()
        return HttpResponse("")
    return HttpResponse("Method not allowed", status=405)


class GardenListView(ListView):
    model = Zone
    template_name = 'core/garden_list.html'
    context_object_name = 'zones'

class GardenDetailView(DetailView):
    model = Zone
    template_name = 'core/garden_detail.html'
    context_object_name = 'zone'
    pk_url_kwarg = 'zone_id'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['core/partials/zone_details_card.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zone = self.get_object()
        context['plants'] = zone.plants.all()
        context['recent_events'] = zone.events.all().order_by('-performed_at')[:10]
        context['watering_frequency'] = calculate_watering_frequency(zone.id)
        
        if self.request.GET.get('edit') == 'true':
            context['form'] = ZoneUpdateForm(instance=zone)
            context['editing'] = True
        else:
            context['form'] = ZoneUpdateForm(instance=zone) # Still pass an unbound form for initial render of display state
            context['editing'] = False
        return context

    def post(self, request, *args, **kwargs):
        zone = self.get_object()
        form = ZoneUpdateForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                # After successful save, render in display mode (editing=False)
                context = self.get_context_data(object=zone) # Re-fetch context to reflect saved data
                context['editing'] = False # Ensure display mode
                return render(request, 'core/partials/zone_details_card.html', context)
            return redirect('garden_detail', zone_id=zone.id)
        else:
            if request.headers.get('HX-Request'):
                # If form is invalid, re-render in editing mode with errors
                context = self.get_context_data(object=zone)
                context['form'] = form # Pass the form with errors
                context['editing'] = True # Stay in editing mode
                return render(request, 'core/partials/zone_details_card.html', context)
            context = self.get_context_data()
            context['form'] = form
            context['editing'] = True # Stay in editing mode
            return render(request, self.template_name, context)
