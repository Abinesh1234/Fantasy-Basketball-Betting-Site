from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Bet, Matchup, Team, Transaction
from .odds import matchup_odds
from .services import BetError, place_bet


class BettingTestCase(TestCase):
    def setUp(self):
        self.t1 = Team.objects.create(espn_id=1, name="Team One")
        self.t2 = Team.objects.create(espn_id=2, name="Team Two")
        self.t3 = Team.objects.create(espn_id=3, name="Team Three")
        self.t4 = Team.objects.create(espn_id=4, name="Team Four")

        # Week 6 is live, week 7 is open for betting
        self.live = Matchup.objects.create(
            week=6, home_team=self.t1, away_team=self.t2, status=Matchup.Status.LIVE
        )
        self.upcoming = Matchup.objects.create(
            week=7, home_team=self.t1, away_team=self.t2, status=Matchup.Status.UPCOMING
        )
        self.my_matchup = Matchup.objects.create(
            week=7, home_team=self.t3, away_team=self.t4, status=Matchup.Status.UPCOMING
        )

        self.user = User.objects.create_user("bettor", password="testpass123")
        self.user.profile.team = self.t3
        self.user.profile.save()

    def balance(self):
        return self.user.profile.balance()


class PlaceBetTests(BettingTestCase):
    def test_starting_balance(self):
        self.assertEqual(self.balance(), 1000)

    def test_valid_bet(self):
        bet = place_bet(self.user, self.upcoming.id, self.t1.id, 100)
        self.assertEqual(self.balance(), 900)
        self.assertEqual(bet.status, Bet.Status.OPEN)
        self.assertTrue(Transaction.objects.filter(bet=bet, amount=-100).exists())

    def test_odds_are_saved_on_bet(self):
        home_odds, _ = matchup_odds(self.upcoming)
        bet = place_bet(self.user, self.upcoming.id, self.t1.id, 100)
        self.assertEqual(bet.odds, home_odds)

    def test_cannot_bet_more_than_balance(self):
        with self.assertRaises(BetError):
            place_bet(self.user, self.upcoming.id, self.t1.id, 1001)
        self.assertEqual(self.balance(), 1000)
        self.assertEqual(Bet.objects.count(), 0)

    def test_cannot_bet_zero_or_negative(self):
        for stake in (0, -50):
            with self.assertRaises(BetError):
                place_bet(self.user, self.upcoming.id, self.t1.id, stake)
        self.assertEqual(self.balance(), 1000)

    def test_cannot_bet_on_own_matchup(self):
        with self.assertRaises(BetError):
            place_bet(self.user, self.my_matchup.id, self.t4.id, 100)
        self.assertEqual(self.balance(), 1000)

    def test_cannot_bet_on_live_matchup(self):
        with self.assertRaises(BetError):
            place_bet(self.user, self.live.id, self.t1.id, 100)

    def test_cannot_bet_on_final_matchup(self):
        self.upcoming.status = Matchup.Status.FINAL
        self.upcoming.save()
        with self.assertRaises(BetError):
            place_bet(self.user, self.upcoming.id, self.t1.id, 100)

    def test_cannot_bet_on_stale_upcoming_week(self):
        # Mislabeled as upcoming, but week 5 is before the live week 6
        stale = Matchup.objects.create(
            week=5, home_team=self.t2, away_team=self.t1, status=Matchup.Status.UPCOMING
        )
        with self.assertRaises(BetError):
            place_bet(self.user, stale.id, self.t1.id, 100)

    def test_cannot_pick_team_not_in_matchup(self):
        with self.assertRaises(BetError):
            place_bet(self.user, self.upcoming.id, self.t3.id, 100)

    def test_cannot_overspend_with_multiple_bets(self):
        place_bet(self.user, self.upcoming.id, self.t1.id, 600)
        with self.assertRaises(BetError):
            place_bet(self.user, self.upcoming.id, self.t2.id, 500)
        self.assertEqual(self.balance(), 400)


class OddsTests(BettingTestCase):
    def test_even_with_no_history(self):
        home, away = matchup_odds(self.upcoming)
        self.assertEqual(home, away)

    def test_better_team_is_favored(self):
        # Team One scores much more than Team Two in past weeks
        for week in range(1, 6):
            Matchup.objects.create(
                week=week, home_team=self.t1, away_team=self.t2,
                home_score=400, away_score=250, status=Matchup.Status.FINAL,
            )
        home, away = matchup_odds(self.upcoming)
        self.assertLess(home, away)  # lower odds = favorite

    def test_probabilities_add_up(self):
        home, away = matchup_odds(self.upcoming)
        self.assertAlmostEqual(1 / home + 1 / away, 1, delta=0.02)


class ViewTests(BettingTestCase):
    def test_pages_require_login(self):
        for name in ("home", "week", "my_bets"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response.url)

    def test_week_page_shows_only_open_matchups(self):
        self.client.login(username="bettor", password="testpass123")
        response = self.client.get(reverse("week"))
        rows = response.context["rows"]
        self.assertEqual({r["matchup"].id for r in rows}, {self.upcoming.id, self.my_matchup.id})

    def test_own_matchup_flagged(self):
        self.client.login(username="bettor", password="testpass123")
        response = self.client.get(reverse("week"))
        mine = next(r for r in response.context["rows"] if r["matchup"].id == self.my_matchup.id)
        self.assertTrue(mine["is_mine"])

    def test_bet_through_view(self):
        self.client.login(username="bettor", password="testpass123")
        self.client.post(reverse("place_bet"), {
            "matchup_id": self.upcoming.id, "team_id": self.t1.id, "stake": 250,
        })
        self.assertEqual(self.balance(), 750)

    def test_garbage_input_rejected(self):
        self.client.login(username="bettor", password="testpass123")
        response = self.client.post(reverse("place_bet"), {"matchup_id": "abc", "stake": "lots"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.balance(), 1000)