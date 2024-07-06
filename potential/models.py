from django.db import models

class Player(models.Model):
    name = models.CharField(max_length=100)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    shots = models.IntegerField(default=0)
    shot_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passes = models.IntegerField(default=0)
    pass_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    dribbles = models.IntegerField(default=0)
    dribbles_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tackles = models.IntegerField(default=0)
    tackle_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    offsides = models.IntegerField(default=0)
    fouls_committed = models.IntegerField(default=0)
    possession_won = models.IntegerField(default=0)
    possession_lost = models.IntegerField(default=0)

    def calculate_potential(self):
        # Implement your logic to calculate potential based on the stored data
        # This is a placeholder; you should define your own algorithm here
        return 0  # Replace with your calculation logic

    def __str__(self):
        return self.name
