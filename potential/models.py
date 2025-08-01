from django.db import models
from datetime import date, datetime

class Player(models.Model):
    CATEGORY_CHOICES = [
        ('training', 'Training'),
        ('official_game', 'Official Game'),
        ('random', 'Random'),
    ]

    name = models.CharField(max_length=100)

    # przechowywane dane (z jednego screena)
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


    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='random'
    )
    training_stats = models.JSONField(default=dict, blank=True)
    official_game_stats = models.JSONField(default=dict, blank=True)
    random_stats = models.JSONField(default=dict, blank=True)
    
    # tabele wagowe z excela - skrócone
    # wymaga rozbudowy w przyszłości (na więcej zdjęć)
    POSITION_WEIGHTS = {
        "Center_Back": [0.01, 0.14, 0.25, 0.25, 0.35],
        "Full_Back": [0.02, 0.20, 0.27, 0.26, 0.25],
        "Offensive_Full_Back": [0.05, 0.24, 0.28, 0.28, 0.15],
        "Defensive_Midfielder": [0.01, 0.24, 0.30, 0.25, 0.20],
        "Midfielder_Allrounder": [0.05, 0.35, 0.35, 0.20, 0.05],
        "Side_Midfielder": [0.15, 0.32, 0.32, 0.16, 0.05],
        "Offensive_Midfielder": [0.15, 0.30, 0.30, 0.20, 0.05],
        "Winger": [0.25, 0.35, 0.27, 0.12, 0.01],
        "Striker": [0.37, 0.30, 0.25, 0.07, 0.01]
    }

    BONUS_GOALS = {
        "Center_Back": 1.2, "Full_Back": 1.2, "Offensive_Full_Back": 1.0, "Defensive_Midfielder": 1.5,
        "Midfielder_Allrounder": 1.0, "Offensive_Midfielder": 0.8, "Side_Midfielder": 1.0,
        "Winger": 0.7, "Striker": 0.6
    }

    BONUS_ASSISTS = {
        "Center_Back": 0.8, "Full_Back": 0.8, "Offensive_Full_Back": 0.8, "Defensive_Midfielder": 0.9,
        "Midfielder_Allrounder": 0.8, "Offensive_Midfielder": 0.7, "Side_Midfielder": 0.8,
        "Winger": 0.7, "Striker": 0.7
    }

    # do wyliczenia jednej zbiorczej
    def calculate_aggregate(self, new_data, category, entry_date=None, position="Unknown"):
        category_field_map = {
            'training': 'training_stats',
            'official_game': 'official_game_stats',
            'random': 'random_stats',
        }

        category_field = category_field_map.get(category)
        if not category_field:
            raise ValueError("Invalid category")

        stats = getattr(self, category_field) or {}

        stats.setdefault("entries", [])
        stats.setdefault("aggregated", {})

        if not entry_date:
            entry_date = date.today()

        entry_date_str = entry_date.strftime('%Y-%m-%d')

        stats["entries"].append({
            "date": entry_date_str,
            "position": position,
            "data": new_data
        })

        for key, value in new_data.items():
            stats["aggregated"][key] = stats["aggregated"].get(key, 0) + value

        stats["total_entries"] = len(stats["entries"])

        stats["last_updated"] = entry_date_str  

        setattr(self, category_field, stats)
        self.save()

    # wszystkie zbiorcze
    def get_all_aggregate_data(self, start_date=None, end_date=None):
        aggregate_data = {}
        stats = set()

        for category, _ in self.CATEGORY_CHOICES:
            category_field = f"{category}_stats"
            stats_data = getattr(self, category_field, {})

            if "aggregated" in stats_data:
                if start_date and end_date:
                    filtered_entries = [
                        entry for entry in stats_data.get("entries", [])
                        if start_date <= datetime.strptime(entry["date"], "%Y-%m-%d").date() <= end_date
                    ]
                else:
                    filtered_entries = stats_data.get("entries", [])

                for entry in filtered_entries:
                    stats.update(entry["data"].keys())

                total_entries = len(filtered_entries)

                aggregated_stats = {key: 0 for key in stats}  # Initialize all stats

                for entry in filtered_entries:
                    for key, value in entry["data"].items():
                        aggregated_stats[key] += value

                # wyliczanie średnich dla statystyk procentowych
                if total_entries > 0:
                    for key in ['shot_accuracy', 'pass_accuracy', 'dribbles_success_rate', 'tackle_success_rate']:
                        aggregated_stats[key] /= total_entries

                    aggregated_stats['average_goals'] = round(aggregated_stats.get('goals', 0) / total_entries, 2)
                    aggregated_stats['average_assists'] = round(aggregated_stats.get('assists', 0) / total_entries, 2)
                    aggregated_stats['average_passes'] = round(aggregated_stats.get('passes', 0) / total_entries, 2)
                    aggregated_stats['average_shots'] = round(aggregated_stats.get('shots', 0) / total_entries, 2)

                # dynamiczna aktualizacja stat
                stats.update([
                    'average_goals', 'average_assists', 'average_passes', 'average_shots'
                ])

                aggregate_data[category] = {
                    "aggregated": aggregated_stats,
                    "entries": filtered_entries,
                    "total_entries": total_entries,
                    "last_updated": stats_data.get("last_updated", "Unknown"),
                }
            else:
                aggregate_data[category] = {"aggregated": {}}

        return aggregate_data, sorted(stats) 

    # zbiorcze dla danej kategorii
    def get_aggregate_data(self, category):
        category_field_map = {
            'training': 'training_stats',
            'official_game': 'official_game_stats',
            'random': 'random_stats',
        }

        category_field = category_field_map.get(category)
        if not category_field:
            raise ValueError("Invalid category")

        stats = getattr(self, category_field, {})

        # weryfikacja czy są jakieś dane
        total_images = stats.get('total_images', 0)

        if total_images > 0:
            stats['average_goals'] = stats.get('goals', 0) / total_images
            stats['average_assists'] = stats.get('assists', 0) / total_images
            stats['average_passes'] = stats.get('passes', 0) / total_images
            stats['average_shots'] = stats.get('shots', 0) / total_images

            stats['average_shot_accuracy'] = stats.get('shot_accuracy', 0) / total_images
            stats['average_pass_accuracy'] = stats.get('pass_accuracy', 0) / total_images
            stats['average_dribbles_success_rate'] = stats.get('dribbles_success_rate', 0) / total_images
            stats['average_tackle_success_rate'] = stats.get('tackle_success_rate', 0) / total_images
        else:
            stats['average_goals'] = 0
            stats['average_assists'] = 0
            stats['average_passes'] = 0
            stats['average_shots'] = 0

            stats['average_shot_accuracy'] = 0
            stats['average_pass_accuracy'] = 0
            stats['average_dribbles_success_rate'] = 0
            stats['average_tackle_success_rate'] = 0

        return stats

    def calculate_position_based_potential(self, start_date=None, end_date=None):
        position_potential_scores = {}

        for category, _ in self.CATEGORY_CHOICES:
            category_field = f"{category}_stats"
            stats = getattr(self, category_field, {})

            if "entries" in stats:
                # filtrowanie wpisów na podstawie daty
                filtered_entries = [
                    entry for entry in stats["entries"]
                    if (not start_date or not end_date or start_date <= datetime.strptime(entry["date"], "%Y-%m-%d").date() <= end_date)
                ]

                for entry in filtered_entries:
                    position = entry.get("position", "Unknown")
                    data = entry["data"]

                    # ochrona przed none
                    if position not in position_potential_scores:
                        position_potential_scores[position] = {}

                    # wyliczenia składowych potencjału
                    attack_score = (
                        self.get_points_for_shots(data.get("shots", 0)) *
                        self.get_points_for_shot_accuracy(data.get("shot_accuracy", 0)) +
                        self.get_points_for_offsides(data.get("offsides", 0))
                    )
                    dribbling_score = (
                        self.get_points_for_dribbles(data.get("dribbles", 0)) *
                        self.get_points_for_dribble_success_rate(data.get("dribbles_success_rate", 0))
                    )
                    passing_score = (
                        self.get_points_for_passes(data.get("passes", 0)) *
                        self.get_points_for_pass_accuracy(data.get("pass_accuracy", 0))
                    )
                    movement_score = (
                        self.get_points_for_possession_won(data.get("possession_won", 0)) +
                        self.get_points_for_possession_lost(data.get("possesion_lost", 0))
                    )
                    defense_score = (
                        self.get_points_for_tackles(data.get("tackles", 0)) *
                        self.get_points_for_tackle_success_rate(data.get("tackle_success_rate", 0)) +
                        self.get_points_for_possession_ratio(data.get("possession_won", 0), data.get("possesion_lost", 0))
                    )

                    # średnia wagowa dla pozycji (z Excela)
                    weights = self.POSITION_WEIGHTS.get(position, [0.2, 0.2, 0.2, 0.2, 0.2])
                    potential_score = (
                        attack_score * weights[0] +
                        dribbling_score * weights[1] +
                        passing_score * weights[2] +
                        movement_score * weights[3] +
                        defense_score * weights[4]
                    )

                    # bonusy
                    potential_score += data.get("goals", 0) * self.BONUS_GOALS.get(position, 0)
                    potential_score += data.get("assists", 0) * self.BONUS_ASSISTS.get(position, 0)

                    # max ocena = 10, do późniejszej analizy
                    potential_score = round(min(potential_score, 10), 3)

                    # Store scores per position-category
                    if category not in position_potential_scores[position]:
                        position_potential_scores[position][category] = []

                    position_potential_scores[position][category].append(potential_score)

        for position in position_potential_scores:
            for category in position_potential_scores[position]:
                scores = position_potential_scores[position][category]
                position_potential_scores[position][category] = round(sum(scores) / len(scores), 2) if scores else "N/A"

        return position_potential_scores

    # Helpery ----->

    def get_points_for_shots(self, shots):
        if shots >= 7:
            return 2
        elif shots == 6:
            return 1.85
        elif shots == 5:
            return 1.6
        elif shots == 4:
            return 1.3
        elif shots == 3:
            return 1.15
        else:
            return 1

    def get_points_for_shot_accuracy(self, accuracy):
        if accuracy <= 10:
            return 0
        elif accuracy <= 20:
            return 0.25
        elif accuracy <= 30:
            return 0.5
        elif accuracy <= 40:
            return 0.75
        elif accuracy <= 49:
            return 1
        elif accuracy <= 55:
            return 1.75
        elif accuracy <= 70:
            return 2.5
        elif accuracy <= 80:
            return 3
        elif accuracy <= 90:
            return 4
        else:
            return 4.5

    def get_points_for_offsides(self, offsides):
        if offsides == 0:
            return 1
        elif offsides == 1:
            return 0.8
        elif offsides == 2:
            return 0.5
        elif offsides == 3:
            return 0
        elif offsides == 4:
            return -1
        else:
            return -2

    def get_points_for_dribbles(self, dribbles):
        """
        Calculate points for dribbles attempted.
        """
        if dribbles >= 22:
            return 2
        elif dribbles >= 20:
            return 1.8
        elif dribbles >= 18:
            return 1.6
        elif dribbles >= 16:
            return 1.4
        elif dribbles >= 14:
            return 1.2
        elif dribbles >= 12:
            return 1
        elif dribbles >= 10:
            return 0.8
        elif dribbles >= 8:
            return 0.6
        elif dribbles >= 6:
            return 0.4
        elif dribbles >= 4:
            return 0.2
        elif dribbles >= 2:
            return 0.1
        else:
            return 0

    def get_points_for_dribble_success_rate(self, success_rate):
        if success_rate <= 10:
            return 0
        elif success_rate <= 20:
            return 0.25
        elif success_rate <= 40:
            return 0.5
        elif success_rate <= 59:
            return 1
        elif success_rate <= 64:
            return 2
        elif success_rate <= 69:
            return 2.5
        elif success_rate <= 74:
            return 3
        elif success_rate <= 85:
            return 3.5
        elif success_rate <= 90:
            return 4
        elif success_rate <= 95:
            return 4.5
        else:
            return 5

    def get_points_for_passes(self, passes):
        if passes >= 24:
            return 2
        elif passes >= 20:
            return 1.8
        elif passes >= 16:
            return 1.6
        elif passes >= 12:
            return 1.4
        elif passes >= 8:
            return 1.2
        elif passes >= 4:
            return 1
        else:
            return 0.8

    def get_points_for_pass_accuracy(self, accuracy):
        if accuracy <= 15:
            return 0
        elif accuracy <= 35:
            return 0.25
        elif accuracy <= 55:
            return 0.5
        elif accuracy <= 70:
            return 0.75
        elif accuracy <= 75:
            return 1
        elif accuracy <= 80:
            return 2
        elif accuracy <= 85:
            return 3
        elif accuracy <= 90:
            return 4
        elif accuracy <= 95:
            return 4.5
        else:
            return 5  

    def get_points_for_possession_won(self, possession_won):
        if possession_won >= 9:
            return 5
        elif possession_won == 8:
            return 4.5
        elif possession_won >= 6:
            return 4
        elif possession_won == 5:
            return 3.5
        elif possession_won == 4:
            return 3
        elif possession_won == 3:
            return 2
        elif possession_won == 2:
            return 1.5
        elif possession_won == 1:
            return 1
        else:
            return 0

    def get_points_for_possession_lost(self, possession_lost):
        if possession_lost >= 8:
            return -2
        elif possession_lost == 7:
            return -1
        elif possession_lost == 6:
            return 0
        elif possession_lost == 5:
            return 1
        elif possession_lost == 4:
            return 2
        elif possession_lost == 3:
            return 3
        elif possession_lost == 2:
            return 3.5
        elif possession_lost == 1:
            return 4
        else:
            return 5

    def get_points_for_tackles(self, tackles):
        if tackles >= 7:
            return 3
        elif tackles == 6:
            return 2.5
        elif tackles == 5:
            return 2
        elif tackles == 4:
            return 1.85
        elif tackles == 3:
            return 1.75
        elif tackles == 2:
            return 1.5
        elif tackles == 1:
            return 1
        else:
            return 0  

    def get_points_for_tackle_success_rate(self, success_rate):
        if success_rate <= 10:
            return 0
        elif success_rate <= 20:
            return 0.1
        elif success_rate <= 30:
            return 0.25
        elif success_rate <= 44:
            return 0.5
        elif success_rate <= 49:
            return 0.75
        elif success_rate <= 60:
            return 1
        elif success_rate <= 70:
            return 1.5
        elif success_rate <= 80:
            return 2
        elif success_rate <= 90:
            return 2.5
        else:
            return 3  

    def get_points_for_possession_ratio(self, possession_won, possession_lost):
        if possession_won > 0 and possession_lost == 0:
            return 1
        if possession_won == 0 and possession_lost == 0:
            return 0

        ratio = possession_won / max(possession_lost, 1)  

        if ratio >= 4:
            return 1
        elif ratio >= 3:
            return 0.75
        elif ratio >= 2:
            return 0.5
        elif ratio >= 1.5:
            return 0.25
        elif ratio >= 1:
            return 0
        elif ratio >= 0.8:
            return -0.25
        elif ratio >= 0.7:
            return -0.5
        elif ratio >= 0.6:
            return -0.75
        elif ratio >= 0.5:
            return -1
        elif ratio >= 0.01:
            return -1.5
        return -2

    def __str__(self):
        # TODO: na razie niepotrzebne
        return self.name

