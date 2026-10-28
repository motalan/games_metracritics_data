# Games Data

An ETL pipeline that scrapes video game data from [Metacritic](https://www.metacritic.com) for one or more release years. It stores the raw HTML pages in an S3-compatible bucket (RustFS) and loads the normalized data into PostgreSQL.

Each execution is recorded as a **scrape run**, and the critic and user scores are saved as a snapshot per run. This keeps the history of how a game's reviews change over time.

## How it works

`main.py` runs these stages in order. Each stage logs its start, its end and how long it took.

1. **create_tables**: creates the database tables and views if they don't exist yet ([core/database.py](core/database.py)).
2. **start_run**: registers a new row in `scrape_run`. The HTML of each run is saved under `data/runs/<run_id>/`.
3. **collect_game_list**: downloads every page of `metacritic.com/browse/game/all/all/<year>/metascore/` for each requested year ([core/extract.py](core/extract.py)). Requests use a random User-Agent and are retried up to 3 times, with a longer wait on `403`/`429` responses.
4. **collect_game_page**: reads the game links from the list pages and downloads each game page, saving it as `<slug>.html` (e.g. `elden-ring.html`).
5. **upload_files_to_s3**: uploads the game pages to `s3://metacritic/runs/<run_id>/game_pages/` ([core/bucket_import.py](core/bucket_import.py)).
6. **load_games**: parses each page ([core/parser.py](core/parser.py)), then normalizes and validates it with the Pydantic `GameInfo` model ([core/transform.py](core/transform.py)). The game is upserted and its review snapshot is saved. If a page fails to parse, the error is logged and the run moves on to the next page.
7. **finish_run**: closes the run with its status (`success` or `failed`), the number of games saved and the finish time.

## Project structure

```
.
├── main.py               # Pipeline entry point (CLI)
├── core/
│   ├── extract.py        # HTTP requests and HTML download
│   ├── parser.py         # HTML parsing with BeautifulSoup
│   ├── transform.py      # Data normalization and the GameInfo model
│   ├── bucket_import.py  # Upload of raw HTML to the S3 bucket
│   └── database.py       # PostgreSQL schema, upserts and snapshots
├── get_games.py          # Legacy script (not used by the pipeline)
├── get_game_info.py      # Legacy script (not used by the pipeline)
├── pyproject.toml
└── data/                 # Generated at runtime (gitignored)
    ├── runs/<run_id>/    # game_list/ and game_pages/ HTML per run
    └── logs/             # One log file per execution
```

> `get_games.py` and `get_game_info.py` are standalone scripts from an earlier version of the project. They rely on `pandas`, which is not listed as a dependency, and on CSS selectors that Metacritic no longer uses.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- An S3-compatible object storage (e.g. RustFS or MinIO) with a bucket named `metacritic`

## Setup

Install the dependencies:

```bash
uv sync
```

Create a `.env` file in the project root:

```env
# PostgreSQL
HOST=localhost
PORT=5432
DATABASE=games
USERNAME=postgres
PASSWORD=your_password

# S3-compatible storage (RustFS)
ENDPOINT_URL=http://localhost:9000
RUSTFS_ACCESS_KEY=your_access_key
RUSTFS_SECRET_KEY=your_secret_key
```

## Usage

```bash
# Scrape games released in the current year
uv run main.py

# Scrape specific release years
uv run main.py --years 2023 2024 2025

# More verbose logging
uv run main.py --years 2025 --log-level DEBUG
```

| Option        | Description                                  | Default      |
|---------------|----------------------------------------------|--------------|
| `--years`     | One or more release years to scrape          | Current year |
| `--log-level` | `DEBUG`, `INFO`, `WARNING` or `ERROR`        | `INFO`       |

Logs are written to the console and to `data/logs/pipeline_<YYYYMMDD_HHMMSS>.log`.

## Database schema

| Table / View            | Description |
|-------------------------|-------------|
| `scrape_run`            | One row per execution: start/finish time, status, years, S3 prefix and number of games scraped |
| `game`                  | One row per game, identified by its Metacritic slug (`/game/elden-ring/`), with name, release date and the run in which it was first seen |
| `platform`              | Platform names |
| `genre`                 | Genre names |
| `company`               | Company names |
| `game_platforms`        | Links games to platforms |
| `game_genres`           | Links games to genres |
| `game_companies`        | Links games to companies, with `bond_type` = `developer` or `publisher` |
| `critic_reviews`        | Critic snapshot per game per run: metascore, positive/mixed/negative counts and the `must_play` flag |
| `users_reviews`         | User snapshot per game per run: user score and positive/mixed/negative counts |
| `latest_critic_reviews` | View with the most recent critic snapshot of each game |
| `latest_users_reviews`  | View with the most recent user snapshot of each game |

Example: the top 10 games by their latest metascore.

```sql
SELECT g.game_name, g.released_date, c.metascore_review, c.must_play
FROM game g
JOIN latest_critic_reviews c USING (game_id)
ORDER BY c.metascore_review DESC NULLS LAST
LIMIT 10;
```

## Collected data

For each game the pipeline collects:

- Name and release date
- Metascore and user score
- Number of positive, mixed and negative reviews (critics and users)
- Platforms and genres
- Developer and publisher
- Whether the game is marked as **Must-Play**

## Notes

- The parser relies on Metacritic's current HTML structure and CSS classes. If the site layout changes, the selectors in [core/parser.py](core/parser.py) need to be updated.
- Scrape responsibly and respect Metacritic's terms of use.
