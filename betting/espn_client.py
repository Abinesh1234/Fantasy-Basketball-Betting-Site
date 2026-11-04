import os
from espn_api.basketball import League

def get_league(debug: bool = False) -> League:
    # Return a connected League object for our private ESPN league.
    return League(
        league_id=int(os.environ["ESPN_LEAGUE_ID"]),
        year=int(os.environ["ESPN_YEAR"]),
        espn_s2=os.environ["ESPN_S2"],
        swid=os.environ["ESPN_SWID"],
        debug=debug,
    )