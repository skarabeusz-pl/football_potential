from django.contrib import admin
from .models import Player

class PlayerAdmin(admin.ModelAdmin):

    list_display = ('name', 'goals', 'assists', 'shots', 'passes')
    exclude = ('training_stats', 'official_game_stats', 'random_stats')

    def save_model(self, request, obj, form, change):
        """
        Ensure JSON fields are initialized as empty dictionaries and numerical stats as zeros.
        """
        if not obj.training_stats:
            obj.training_stats = {}
        if not obj.official_game_stats:
            obj.official_game_stats = {}
        if not obj.random_stats:
            obj.random_stats = {}

        # ustawiamy na 0 - wtedy widać puste staty w panelu admina
        # pozwala na edycję w panelu admina
        for field in ['goals', 'assists', 'shots', 'shot_accuracy', 'passes', 'pass_accuracy',
                      'dribbles', 'dribbles_success_rate', 'tackles', 'tackle_success_rate',
                      'offsides', 'fouls_committed', 'possession_won', 'possession_lost']:
            if getattr(obj, field) is None:
                setattr(obj, field, 0)

        super().save_model(request, obj, form, change)

admin.site.register(Player, PlayerAdmin)
