from django.contrib import admin
from .models import Team, Matchup, UserProfile, Bet, Transaction

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "balance")


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ("user", "matchup", "pick", "stake", "odds", "status", "created_at")
    list_filter = ("status", "matchup__week")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "reason", "bet", "created_at")
    list_filter = ("user",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "wins", "losses", "ties")


@admin.register(Matchup)
class MatchupAdmin(admin.ModelAdmin):
    list_display = ("week", "home_team", "away_team", "home_score", "away_score", "status")
    list_filter = ("week", "status")
