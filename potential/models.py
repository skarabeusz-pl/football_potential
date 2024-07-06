from django.db import models

class Player(models.Model):
    name = models.CharField(max_length=100)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    shots = models.IntegerField(default=0)
    shot_accuracy = models.IntegerField(default=0)
    passes = models.IntegerField(default=0)
    pass_accuracy = models.IntegerField(default=0)
    dribbles = models.IntegerField(default=0)
    dribbles_success_rate = models.IntegerField(default=0)
    tackles = models.IntegerField(default=0)
    tackle_success_rate = models.IntegerField(default=0)
    offsides = models.IntegerField(default=0)
    fouls_committed = models.IntegerField(default=0)
    possession_won = models.IntegerField(default=0)
    possession_lost = models.IntegerField(default=0)

    def calculate_potential(self):
        # Example potential calculation logic
        total_contributions = (
            self.goals + self.assists + self.shots + self.shot_accuracy +
            self.passes + self.pass_accuracy + self.dribbles + self.dribbles_success_rate +
            self.tackles + self.tackle_success_rate + self.offsides + self.fouls_committed +
            self.possession_won + self.possession_lost
        )
        # Example: Normalize to a scale of 0 to 10
        potential = min(max(total_contributions / 100, 0), 10)
        return potential
