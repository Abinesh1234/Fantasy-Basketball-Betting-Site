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

            # Pairings: scoreboard() is correct for every week, including future ones
            try:
                pairings = league.scoreboard(week)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Week {week}: skipped ({e})"))
                continue

            # Scores: box_scores() is only correct up to the current week
            scores = {}
            if week <= current:
                try:
                    for b in league.box_scores(matchup_period=week):
                        if b.home_team and b.away_team:
                            scores[(b.home_team.team_id, b.away_team.team_id)] = (
                                b.home_score or 0,
                                b.away_score or 0,
                            )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Week {week}: no scores ({e})"))

            count = 0
            seen_ids = []
            for m in pairings:
                home_id = getattr(m.home_team, "team_id", None)
                away_id = getattr(m.away_team, "team_id", None)
                home = teams_by_espn_id.get(home_id)
                away = teams_by_espn_id.get(away_id)
                if not home or not away:  # bye week or unknown team
                    continue

                home_score, away_score = scores.get((home_id, away_id), (0, 0))
                matchup, _ = Matchup.objects.update_or_create(
                    week=week,
                    home_team=home,
                    away_team=away,
                    defaults={
                        "home_score": home_score,
                        "away_score": away_score,
                        "status": status,
                    },
                )
                seen_ids.append(matchup.id)
                count += 1

            # Remove matchups ESPN no longer lists for this week
            for m in Matchup.objects.filter(week=week).exclude(id__in=seen_ids):
                if m.bets.exists():
                    self.stdout.write(self.style.WARNING(f"Stale matchup with bets, review in admin: {m}"))
                else:
                    m.delete()

            self.stdout.write(self.style.SUCCESS(f"Synced {count} matchups for week {week} ({status})"))