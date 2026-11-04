from django.db import models

# Create your models here.


class Team(models.Model):
    espn_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    owner = models.CharField(max_length=100, blank=True)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    ties = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Matchup(models.Model):
    week = models.IntegerField()
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_matchups")
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="away_matchups")
    home_score = models.FloatField(default=0)
    away_score = models.FloatField(default=0)

    class Meta:
        unique_together = ("week", "home_team", "away_team")

    def __str__(self):
        return f"Week {self.week}: {self.home_team} vs {self.away_team}"