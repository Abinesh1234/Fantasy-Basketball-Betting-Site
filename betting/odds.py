import math
from statistics import mean, pstdev
from .models import Matchup

PRIOR_WEEKS = 3
DEFAULT_SD = 40.0
MIN_PROB, MAX_PROB = 0.05, 0.95
HOUSE_EDGE = 0.0

def _team_scores():
    scores = {}
    for m in Matchup.objects.filter(status=Matchup.Status.FINAL):
        scores.setdefault(m.home_team_id, []).append(m.home_score)
        scores.setdefault(m.away_team_id, []).append(m.away_score)
    return scores

def _normal_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))

def matchup_odds(matchup):
    """Return (home_odds, away_odds) as decimal odds for a matchup."""
    scores = _team_scores()
    all_scores = [s for team in scores.values() for s in team]
    if not all_scores:
        even = round(1 / (0.5) * (1 + HOUSE_EDGE), 2)
        return even, even

    league_avg = mean(all_scores)
    league_sd = pstdev(all_scores) or DEFAULT_SD

    def rating(team_id):
        s = scores.get(team_id, [])
        n = len(s)
        avg = (sum(s) + PRIOR_WEEKS * league_avg) / (n + PRIOR_WEEKS)
        sd = pstdev(s) if n >= 3 else league_sd
        return avg, sd

    home_avg, home_sd = rating(matchup.home_team_id)
    away_avg, away_sd = rating(matchup.away_team_id)

    spread = math.sqrt(home_sd**2 + away_sd**2) or DEFAULT_SD
    p_home = _normal_cdf((home_avg - away_avg) / spread)
    p_home = min(max(p_home, MIN_PROB), MAX_PROB)
    p_away = 1 - p_home

    def to_odds(p):
        return round(1 / (p * (1 + HOUSE_EDGE)), 2)

    return to_odds(p_home), to_odds(p_away)