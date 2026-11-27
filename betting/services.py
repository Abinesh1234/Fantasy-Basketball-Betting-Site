from django.db import transaction

from .models import Bet, Matchup, Team, Transaction, first_open_week
from .odds import matchup_odds


class BetError(Exception):
    pass


def place_bet(user, matchup_id, team_id, stake):
    with transaction.atomic():
        try:
            matchup = Matchup.objects.select_related("home_team", "away_team").get(pk=matchup_id)
        except Matchup.DoesNotExist:
            raise BetError("That matchup doesn't exist.")

        if matchup.status != Matchup.Status.UPCOMING or matchup.week < first_open_week():
            raise BetError("Betting is closed for this matchup.")

        if team_id == matchup.home_team_id:
            pick = matchup.home_team
        elif team_id == matchup.away_team_id:
            pick = matchup.away_team
        else:
            raise BetError("That team isn't in this matchup.")

        my_team = user.profile.team
        if my_team and my_team.id in (matchup.home_team_id, matchup.away_team_id):
            raise BetError("You can't bet on your own matchup.")

        if stake <= 0:
            raise BetError("Stake must be more than 0.")
        if stake > user.profile.balance():
            raise BetError("You too broke for that")

        # Odds are calculated on the server, never taken from the form
        home_odds, away_odds = matchup_odds(matchup)
        odds = home_odds if pick == matchup.home_team else away_odds

        bet = Bet.objects.create(user=user, matchup=matchup, pick=pick, stake=stake, odds=odds)
        Transaction.objects.create(
            user=user, amount=-stake, reason=f"Bet on {pick.name} (wk {matchup.week})", bet=bet
        )
        return bet