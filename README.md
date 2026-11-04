# Fantasy Basketball Betting Site

Built with Django, using [cwendt94/espn-api](https://github.com/cwendt94/espn-api) to pull league data from ESPN.

## How it works

- A sync command pulls teams, matchups and scores from ESPN into the local database.
- Users bet coins on upcoming matchups. Betting locks once a matchup goes live.
- When a matchup is final, bets are settled and winners are paid out.
- Balances are calculated from a ledger of transactions, so every credit and debit is recorded.

## Setup for Collaborators

### 1. Clone the repo

```bash
git clone https://github.com/Abinesh1234/Fantasy-Basketball-Betting-Site.git
cd Fantasy-Basketball-Betting-Site
```

### 2. Create an environment and install dependencies

Requires Python 3.13.

**With conda:**

```bash
conda create -n fantasybets python=3.13 -y
conda activate fantasybets
pip install -r requirements.txt
```

**Without conda:**

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Activate the environment every time you open a new terminal for this project.

### 3. Create your `.env`

```bash
cp .env.example .env
```

Then fill in the values:

| Variable | What to put |
|---|---|
| `DJANGO_SECRET_KEY` | Generate your own (command below). Wrap it in single quotes. |
| `DJANGO_DEBUG` | `True` for local development |
| `ESPN_LEAGUE_ID` | The `leagueId=` number in the league page URL |
| `ESPN_YEAR` | The season's ending year (e.g. `2027` for 2026–27) |
| `ESPN_S2` | Your `espn_s2` cookie (see below) |
| `ESPN_SWID` | Your `SWID` cookie, **including the curly braces** |

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Finding your ESPN cookies:** log in to ESPN Fantasy, open the league page, open DevTools (Cmd+Option+I on Mac, F12 on Windows), go to **Application → Cookies → https://fantasy.espn.com**, and copy `espn_s2` and `SWID`.

Use your own cookies if you're in the league. They act like your ESPN login, so never commit them or post them anywhere. If the ESPN sync starts failing, your cookies have probably expired; copy fresh ones.

### 4. Set up the database and run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py sync_espn
python manage.py runserver
```

Open http://127.0.0.1:8000/admin and log in to check that teams and matchups loaded.

### 5. VS Code

Select the project's interpreter: **Cmd+Shift+P → Python: Select Interpreter**, then choose `fantasybets` (or `.venv`). This fixes "Import could not be resolved" warnings.

## Project structure

```
├── .env.example                  # template for required environment variables
├── manage.py
├── requirements.txt
├── fantasy_bets/
│   ├── settings.py               # reads secrets from .env
│   └── urls.py
└── betting/
    ├── espn_client.py            # get_league(): the only place that connects to ESPN
    ├── models.py                 # Team, Matchup, UserProfile, Bet, Transaction
    ├── admin.py
    └── management/commands/
        └── sync_espn.py          # pulls ESPN data into the database
```

## Working together

- **Each person has their own local database.** Your test users and bets won't show up for anyone else.
- **Use branches and pull requests** instead of pushing straight to `main`:
  ```bash
  git checkout -b my-feature
  # ...make changes...
  git push -u origin my-feature
  ```
- **Changed `models.py`?** Run `python manage.py makemigrations` and commit the new migration file. After pulling someone else's migration, run `python manage.py migrate`.
- **Installed a new package?** Run `pip freeze > requirements.txt` and commit it. After pulling, run `pip install -r requirements.txt`.
- **Never commit `.env` or `db.sqlite3`.** Both are already in `.gitignore`.

## Package docs

The [espn-api wiki](https://github.com/cwendt94/espn-api/wiki) documents the `League` object and everything it returns. The basketball page is the one we use: [League Class Basketball](https://github.com/cwendt94/espn-api/wiki/League-Class-Basketball).
