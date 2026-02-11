from django.contrib import admin
from django.utils.html import format_html
from .models import Zone, Species, Plant, IngestQueue, GardenEvent, FertilizerRecipe

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'sunlight_level', 'size_m2', 'irrigation_type', 'sun_hours')
    list_filter = ('sunlight_level', 'irrigation_type')
    search_fields = ('name',)

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_days_to_maturity', 'created_at')
    search_fields = ('name', 'description')

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'zone', 'status')
    list_filter = ('species', 'zone', 'status')
    search_fields = ('name',)

@admin.register(IngestQueue)
class IngestQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'raw_text_summary', 'predicted_action', 'processed', 'has_audio', 'created_at')
    list_filter = ('processed', 'predicted_action')
    search_fields = ('raw_text', 'transcript_clean')
    readonly_fields = ('audio_player',)

    def raw_text_summary(self, obj):
        return (obj.transcript_clean or obj.raw_text)[:50]
    raw_text_summary.short_description = 'Text Summary'

    def has_audio(self, obj):
        return bool(obj.audio_file)
    has_audio.boolean = True
    has_audio.short_description = 'Audio'

    def audio_player(self, obj):
        if obj.audio_file:
            return format_html('<audio controls src="{}"></audio>', obj.audio_file.url)
        return "No audio file"
    audio_player.short_description = 'Audio Player'

@admin.register(GardenEvent)
class GardenEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'plant', 'zone', 'performed_at')
    list_filter = ('event_type', 'zone', 'performed_at')
    search_fields = ('plant__name', 'metadata')

@admin.register(FertilizerRecipe)
class FertilizerRecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'ingredients')
