from django import forms
from .models import Player

class UploadImageForm(forms.Form):
    image = forms.ImageField()

class PlayerSelectForm(forms.Form):
    player = forms.ModelChoiceField(queryset=Player.objects.all(), required=True)