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
        parser.add_argument("--week", type=int, help="Sync a single week (default: all weeks through next week)")

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
                    "name": t.team_name.strip(),
                    "owner": owner_name(t),
                    "wins": getattr(t, "wins", 0),
                    "losses": getattr(t, "losses", 0),
                    "ties": getattr(t, "ties", 0),
                },
            )
            teams_by_espn_id[t.team_id] = obj
        self.stdout.write(self.style.SUCCESS(f"Synced {len(teams_by_espn_id)} teams"))

        # Matchups
        current = league.currentMatchupPeriod
        weeks = [options["week"]] if options["week"] else range(1, current + 2)

        for week in weeks:
            if week < current:
                status = Matchup.Status.FINAL
            elif week == current:
                status = Matchup.Status.LIVE
            else:
                status = Matchup.Status.UPCOMING

            try:
                boxes = league.box_scores(matchup_period=week)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Week {week}: skipped ({e})"))
                continue

            count = 0
            for box in boxes:
                if not box.home_team or not box.away_team:  # bye week
                    continue
                home = teams_by_espn_id.get(box.home_team.team_id)
                away = teams_by_espn_id.get(box.away_team.team_id)
                if not home or not away:
                    continue
                Matchup.objects.update_or_create(
                    week=week,
                    home_team=home,
                    away_team=away,
                    defaults={
                        "home_score": box.home_score or 0,
                        "away_score": box.away_score or 0,
                        "status": status,
                    },
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f"Synced {count} matchups for week {week} ({status})"))