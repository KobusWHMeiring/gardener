from django.db import models
from django.utils import timezone

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Zone(TimeStampedModel):
    class SunlightLevel(models.TextChoices):
        FULL_SUN = 'FULL_SUN', 'Full Sun'
        PARTIAL = 'PARTIAL', 'Partial'
        SHADE = 'SHADE', 'Shade'

    class IrrigationType(models.TextChoices):
        DRIP = 'DRIP', 'Drip'
        MANUAL = 'MANUAL', 'Manual'
        SPRINKLER = 'SPRINKLER', 'Sprinkler'
        NONE = 'NONE', 'None'

    name = models.CharField(max_length=100)
    sunlight_level = models.CharField(
        max_length=20,
        choices=SunlightLevel.choices,
        default=SunlightLevel.FULL_SUN
    )
    size_m2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    irrigation_type = models.CharField(
        max_length=20,
        choices=IrrigationType.choices,
        default=IrrigationType.NONE,
        null=True,
        blank=True
    )
    sun_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return self.name

class Species(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    default_days_to_maturity = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Species"

class FertilizerRecipe(TimeStampedModel):
    name = models.CharField(max_length=100)
    ingredients = models.TextField()
    instructions = models.TextField()

    def __str__(self):
        return self.name

class Plant(TimeStampedModel):
    class Status(models.TextChoices):
        SEEDLING = 'SEEDLING', 'Seedling'
        GERMINATED = 'GERMINATED', 'Germinated'
        PLANTED = 'PLANTED', 'Planted'
        PROVIDING = 'PROVIDING', 'Providing'
        REMOVED = 'REMOVED', 'Removed'

    name = models.CharField(max_length=100)
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True, blank=True, related_name='instances')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='plants')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SEEDLING
    )

    def __str__(self):
        return self.name

class IngestQueue(TimeStampedModel):
    source_file = models.FileField(upload_to='uploads/%Y/%m/', null=True, blank=True)
    audio_file = models.FileField(upload_to='ingest/audio/', null=True, blank=True)
    raw_text = models.TextField(blank=True)
    transcript_clean = models.TextField(blank=True, help_text="AI cleaned version (no fluff)")
    predicted_action = models.CharField(max_length=100, blank=True)
    predicted_data = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Ingest Item {self.id} ({'Processed' if self.processed else 'Pending'})"

class GardenEvent(TimeStampedModel):
    class EventType(models.TextChoices):
        WATER = 'WATER', 'Water'
        PLANT = 'PLANT', 'Plant'
        SOW = 'SOW', 'Sow'
        GERMINATE = 'GERMINATE', 'Germinate'
        TRANSPLANT = 'TRANSPLANT', 'Transplant'
        FIRST_HARVEST = 'FIRST_HARVEST', 'First Harvest'
        TERMINATE = 'TERMINATE', 'Terminate'
        NOTE = 'NOTE', 'Note'
        HARVEST = 'HARVEST', 'Harvest'
        FERTILIZE = 'FERTILIZE', 'Fertilize'
        HEALTH_CHECK = 'HEALTH_CHECK', 'Health Check'

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    performed_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    parent_event = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_events')
    recipe = models.ForeignKey(FertilizerRecipe, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')

    def __str__(self):
        return f"{self.event_type} at {self.zone.name}"