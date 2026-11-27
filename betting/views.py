from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView, TemplateView
from .models import Bet, Matchup
from .odds import matchup_odds
from .services import BetError, place_bet

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        context["profile"] = profile
        context["balance"] = profile.balance()
        return context

class WeekView(LoginRequiredMixin, TemplateView):
    template_name = "week.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        my_team = self.request.user.profile.team
        rows = []
        matchups = Matchup.objects.filter(status=Matchup.Status.UPCOMING).select_related(
            "home_team", "away_team"
        ).order_by("week")
        for m in matchups:
            home_odds, away_odds = matchup_odds(m)
            rows.append({
                "matchup": m,
                "home_odds": home_odds,
                "away_odds": away_odds,
                "is_mine": my_team is not None and my_team.id in (m.home_team_id, m.away_team_id),
            })
        context["rows"] = rows
        context["balance"] = self.request.user.profile.balance()
        return context


class PlaceBetView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            matchup_id = int(request.POST["matchup_id"])
            team_id = int(request.POST["team_id"])
            stake = int(request.POST["stake"])
        except (KeyError, ValueError):
            messages.error(request, "Invalid bet.")
            return redirect("week")

        try:
            bet = place_bet(request.user, matchup_id, team_id, stake)
        except BetError as e:
            messages.error(request, str(e))
        else:
            messages.success(
                request, f"Bet placed: {bet.stake} on {bet.pick.name} at {bet.odds} (pays {bet.payout()})"
            )
        return redirect("week")


class MyBetsView(LoginRequiredMixin, ListView):
    template_name = "my_bets.html"
    context_object_name = "bets"

    def get_queryset(self):
        return (
            Bet.objects.filter(user=self.request.user)
            .select_related("matchup__home_team", "matchup__away_team", "pick")
            .order_by("-created_at")
        )