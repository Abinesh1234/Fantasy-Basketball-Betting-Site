from django.core.management.base import BaseCommand, CommandError

from betting.espn_client import get_league
from betting.models import Matchup, Team


def owner_name(team):
    owners = getattr(team, "owners", None)
    if owners:
        first = owners[0]
        if isinstance(first, dict):
            return f"{first.get('firstName', '')} {first.get('lastName', '')}".strip()
        return str(first)
    return str(getattr(team, "owner", "") or "")


class Command(BaseCommand):
    help = "Sync teams and matchups from the ESPN fantasy league"

    def add_arguments(self, parser):
        parser.add_argument("--week", type=int, help="Matchup week (default: current)")

    def handle(self, *args, **options):
        try:
            league = get_league()
        except KeyError as e:
            raise CommandError(f"Missing environment variable: {e}")
        except Exception as e:
            raise CommandError(f"Could not connect to ESPN: {e}")

        # Teams
        teams_by_espn_id = {}
        for t in league.teams:
            obj, _ = Team.objects.update_or_create(
                espn_id=t.team_id,
                defaults={
                    "name": t.team_name,
                    "owner": owner_name(t),
                    "wins": getattr(t, "wins", 0),
                    "losses": getattr(t, "losses", 0),
                    "ties": getattr(t, "ties", 0),
                },
            )
            teams_by_espn_id[t.team_id] = obj
        self.stdout.write(self.style.SUCCESS(f"Synced {len(teams_by_espn_id)} teams"))

        # Matchups
        week = options["week"] or league.currentMatchupPeriod
        count = 0
        for m in league.scoreboard(week):
            home = teams_by_espn_id.get(m.home_team.team_id)
            away = teams_by_espn_id.get(m.away_team.team_id)
            if not home or not away:
                continue
            Matchup.objects.update_or_create(
                week=week,
                home_team=home,
                away_team=away,
                defaults={
                    "home_score": getattr(m, "home_final_score", 0) or 0,
                    "away_score": getattr(m, "away_final_score", 0) or 0,
                },
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Synced {count} matchups for week {week}"))