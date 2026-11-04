from django.contrib import admin
from .models import Team, Matchup

# Register your models here.


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "wins", "losses", "ties")


@admin.register(Matchup)
class MatchupAdmin(admin.ModelAdmin):
    list_display = ("week", "home_team", "away_team", "home_score", "away_score")
    list_filter = ("week",)
