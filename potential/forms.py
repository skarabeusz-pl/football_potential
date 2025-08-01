from django import forms
from .models import Player
from datetime import date


class UploadImageForm(forms.Form):
    image = forms.ImageField(required=True)
    category = forms.ChoiceField(
        choices=Player.CATEGORY_CHOICES,
        required=True,
        label="Category"
    )
    entry_date = forms.DateField(
        initial=date.today,  # Default to today's date
        widget=forms.DateInput(attrs={"type": "date"})
    )


class PlayerSelectForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.all(),
        required=True
    )
