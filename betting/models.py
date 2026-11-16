from django.db import models
from django.conf import settings
from django.db.models import Sum

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
    class Status(models.TextChoices):
        UPCOMING = "upcoming"
        LIVE = "live"
        FINAL = "final"

    week = models.IntegerField()
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_matchups")
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="away_matchups")
    home_score = models.FloatField(default=0)
    away_score = models.FloatField(default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)

    class Meta:
        unique_together = ("week", "home_team", "away_team")

    def __str__(self):
        return f"Week {self.week}: {self.home_team} vs {self.away_team}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    team = models.OneToOneField(Team, on_delete=models.SET_NULL, null=True, blank=True)

    def balance(self):
        return self.user.transactions.aggregate(total=Sum("amount"))["total"] or 0

    def __str__(self):
        return self.user.username


class Bet(models.Model):
    class Status(models.TextChoices):
        OPEN = "open"
        WON = "won"
        LOST = "lost"
        PUSH = "push"  # tie, stake refunded

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bets")
    matchup = models.ForeignKey(Matchup, on_delete=models.CASCADE, related_name="bets")
    pick = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="bets_on")
    stake = models.PositiveIntegerField()
    odds = models.FloatField()  # decimal odds: 1.8 means a win pays 1.8x the stake
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def payout(self):
        return round(self.stake * self.odds)

    def __str__(self):
        return f"{self.user} – {self.stake} on {self.pick} (wk {self.matchup.week})"


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    amount = models.IntegerField()  # positive = credit, negative = debit
    reason = models.CharField(max_length=100)
    bet = models.ForeignKey(Bet, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.amount:+} ({self.reason})"