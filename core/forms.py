from django import forms
from core.models import Zone, FertilizerRecipe

class ZoneUpdateForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['name', 'size_m2', 'irrigation_type', 'sun_hours', 'sunlight_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'size_m2': forms.NumberInput(attrs={'class': 'form-control'}),
            'irrigation_type': forms.Select(attrs={'class': 'form-control'}),
            'sun_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'sunlight_level': forms.Select(attrs={'class': 'form-control'}),
        }

class FertilizerRecipeForm(forms.ModelForm):
    class Meta:
        model = FertilizerRecipe
        fields = ['name', 'ingredients', 'instructions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

