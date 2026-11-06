# Games Data

An ETL pipeline that scrapes video game data from [Metacritic](https://www.metacritic.com) for one or more release years. The raw HTML pages are stored only in an S3-compatible bucket (RustFS), never on the local disk, and every parsing step reads them back from the bucket before loading the normalized data into PostgreSQL.

Each execution is recorded as a **scrape run**, and the critic and user scores are saved as a snapshot per run. This keeps the history of how a game's reviews change over time. In the bucket, the pages are organized by the **date** of the execution, so the history can be browsed by period.

## How it works

`main.py` runs these stages in order. Each stage logs its start, its end and how long it took. Stage 1 runs once; stages 2–6 run once per requested year, and one year finishes before the next one starts (e.g. `--years 1996 1997` processes all of 1996, then all of 1997).

1. **create_tables**: creates the database tables and views if they don't exist yet ([core/database.py](core/database.py)).
2. **start_run**: registers a new row in `scrape_run` for the year (`years` holds that single year) with its bucket prefix, `runs/<YYYY-MM-DD>/<year>/`.
3. **collect_game_list**: downloads every page of `metacritic.com/browse/game/all/all/<year>/metascore/` and uploads it straight to `<prefix>game_list/` ([core/extract.py](core/extract.py)). Requests use a random User-Agent and are retried up to 3 times, with a longer wait on `403`/`429` responses. A page that can't be fetched is logged and skipped.
4. **collect_game_page**: reads the list pages back from the bucket, extracts the game links and uploads each game page to `<prefix>game_pages/<slug>.html` (e.g. `elden-ring.html`).
5. **load_games**: reads each game page from the bucket, parses it ([core/parser.py](core/parser.py)), then normalizes and validates it with the Pydantic `GameInfo` model ([core/transform.py](core/transform.py)). The game is upserted and its review snapshot is saved. If a page fails to parse, the error is logged and the run moves on to the next page. At the end of the year it logs how many games are missing each field, with a warning when a field is missing for every game.
6. **finish_run**: closes the run with its status (`success` or `failed`), the number of games saved and the finish time. A failed year is logged and the pipeline moves on to the next year.

## Bucket layout

All pages go to the `metacritic` bucket, grouped by the date the pipeline ran and then by release year. The date is taken once at the start, so every year of the same execution shares it.

```
metacritic/
└── runs/
    └── 2026-11-05/                  # execution date
        └── 2024/                    # release year
            ├── game_list/
            │   ├── y_2024_pg_1.html
            │   └── y_2024_pg_2.html
            └── game_pages/
                ├── elden-ring.html
                └── astro-bot.html
```

Running the pipeline again on the same day overwrites that day's pages. Each execution still gets its own `scrape_run` row and review snapshot in the database.

[core/bucket_import.py](core/bucket_import.py) holds the bucket helpers: `run_prefix` builds the prefix, `upload_content` uploads a page kept in memory, `list_files` lists the keys under a prefix (with pagination) and `read_file` returns a page's HTML.

## Project structure

```
.
├── main.py               # Pipeline entry point (CLI)
├── core/
│   ├── extract.py        # HTTP requests and HTML download
│   ├── parser.py         # HTML parsing with BeautifulSoup
│   ├── transform.py      # Data normalization and the GameInfo model
│   ├── bucket_import.py  # Upload, listing and reading of raw HTML in the S3 bucket
│   └── database.py       # PostgreSQL schema, upserts and snapshots
├── pyproject.toml
└── data/                 # Generated at runtime (gitignored)
    └── logs/             # One log file per execution (the only local output)
```

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
| `game`                  | One row per game, identified by its Metacritic slug (`/game/elden-ring/`), with name, release date, description, age rating (`content_rating`, e.g. `T`), image link (`image_url`) and the run in which it was first seen |
| `platform`              | Platform names |
| `genre`                 | Genre names |
| `company`               | Company names |
| `game_platforms`        | Links games to platforms |
| `game_genres`           | Links games to genres |
| `game_companies`        | Links games to companies, with `bond_type` = `developer` or `publisher` |
| `critic_reviews`        | Critic snapshot per game per run: metascore, positive/mixed/negative counts and the `must_play` flag |
| `users_reviews`         | User snapshot per game per run: user score (multiplied by 10, e.g. `8.8` → `88`) and positive/mixed/negative counts |
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
- Description, age rating (ESRB) and the link to the game image (the image itself is not downloaded)
- Metascore and user score
- Number of positive, mixed and negative reviews (critics and users)
- Platforms and genres
- Developer and publisher
- Whether the game is marked as **Must-Play**

Not every page has all of these details. Only the name and the Must-Play flag are required. Every field typed as `| None` in `GameInfo` is stored as `NULL`:

| Missing on the page | Stored as |
|---------------------|-----------|
| Release date, or a text like `TBA` | `game.released_date` = `NULL` |
| Metascore or critic review counts | `NULL` columns in `critic_reviews` |
| User score or user review counts | `NULL` columns in `users_reviews` |
| Developer or publisher | No row in `game_companies` for that role |
| Genres or platforms | No rows in `game_genres` / `game_platforms` |
| Description, age rating or image | `NULL` columns in `game` |

## Notes

- The parser reads the game page in this order ([core/parser.py](core/parser.py)):
  - the schema.org `VideoGame` JSON-LD embedded in the page: name, release date, platforms, genres, first publisher, metascore, description, age rating and image link;
  - the `data-testid` attributes: developer, critic and user scores, review counts and the Must-Play badge;
  - the `game-details` section, as a fallback for the JSON-LD fields.

  These sources depend less on CSS classes, but they can still change. If the log warns that a field is missing for every game of a year, the selectors need to be updated.
- Scrape responsibly and respect Metacritic's terms of use.
