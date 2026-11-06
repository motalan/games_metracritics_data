import argparse
import logging
import os
import time
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime
from tqdm import tqdm
from dotenv import load_dotenv
from core.extract import collect_game_list, collect_game_page
from core.parser import get_game_info
from core.transform import data_normalization
from core.bucket_import import list_files, read_file, run_prefix
from core.database import create_connection, create_tables, start_run, finish_run, upsert_game, save_snapshot

load_dotenv()

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Metacritic games scraping pipeline")
    parser.add_argument('--years', nargs='+', type=int, default=[date.today().year], help="Release years to scrape (default: current year)")
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    return parser.parse_args()

# Log to the console and to a file per execution
def setup_logging(level: str, log_dir: str = 'data/logs') -> str:
    os.makedirs(log_dir, exist_ok=True)
    log_file = f'{log_dir}/pipeline_{datetime.now():%Y%m%d_%H%M%S}.log'

    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding='utf-8')]
    )

    return log_file

# Log the start, the end and the duration of a pipeline stage
@contextmanager
def stage(name: str):
    logger.info(f"[{name}] started")
    start = time.perf_counter()
    yield
    logger.info(f"[{name}] finished in {time.perf_counter() - start:.1f}s")

# Fields checked after loading a year: if one is empty for every game, the page layout probably changed
TRACKED_FIELDS = ['released_date', 'metascore_review', 'user_review', 'developer', 'publisher', 'genres', 'platforms', 'description', 'content_rating', 'image_url']

# Log how many games are missing each tracked field, warning when a field is missing for all of them
def log_missing_fields(missing: Counter, saved: int):
    if saved == 0:
        return

    logger.info("Games missing each field: " + ", ".join(f"{field}={missing[field]}" for field in TRACKED_FIELDS))

    for field in TRACKED_FIELDS:
        if saved > 1 and missing[field] == saved:
            logger.warning(f"Field '{field}' is missing for all {saved} games: the parser selector probably broke after a Metacritic layout change.")

# Read every game page of the run from the bucket and save it in the database, returning how many games were saved
def load_games(connection, run_id: int, prefix: str) -> int:
    saved = 0
    failed = 0
    missing = Counter()

    for key in tqdm(list_files(f'{prefix}game_pages/'), desc="Loading games"):
        # Game pages are saved by slug (.../game_pages/elden-ring.html -> /game/elden-ring/)
        game_slug = f'/game/{key.rsplit("/", 1)[-1].removesuffix(".html")}/'

        try:
            game = data_normalization(get_game_info(read_file(key)))

            game_id = upsert_game(connection, game, game_slug, run_id)
            save_snapshot(connection, run_id, game_id, game)
            saved += 1
            missing.update(field for field in TRACKED_FIELDS if getattr(game, field) in (None, []))
            logger.debug(f"Saved {game_slug} (game_id={game_id}).")

        except Exception:
            # A page with an unexpected layout must not stop the whole run
            connection.rollback()
            failed += 1
            logger.exception(f"Failed to load {key}.")

    logger.info(f"{saved} games saved, {failed} failed.")
    log_missing_fields(missing, saved)

    return saved

# Run the full pipeline for a single year as its own scrape run, returning its status and how many games were saved
def run_year(connection, year: int, run_date: date) -> tuple[str, int]:
    run_start = time.perf_counter()

    # The HTML is stored in the bucket by execution date and release year (a second run on the same day overwrites it)
    prefix = run_prefix(run_date, year)
    run_id = start_run(connection, [year], prefix)
    logger.info(f"Scrape run {run_id} started for year {year}, pages stored in {prefix}.")

    status = 'failed'
    games_scraped = 0

    try:
        with stage('collect_game_list'):
            list_pages = collect_game_list(year, prefix)
        logger.info(f"{list_pages} list pages saved in {prefix}game_list/.")

        with stage('collect_game_page'):
            game_pages = collect_game_page(prefix)
        logger.info(f"{game_pages} game pages saved in {prefix}game_pages/.")

        with stage('load_games'):
            games_scraped = load_games(connection, run_id, prefix)

        status = 'success'

    except Exception:
        # A failed year must not stop the following years
        logger.exception(f"Scrape run {run_id} (year {year}) failed.")

    finally:
        connection.rollback()  # Discard any transaction left open by a failure
        finish_run(connection, run_id, status, games_scraped)
        logger.info(f"Scrape run {run_id} (year {year}) finished with status '{status}': {games_scraped} games in {time.perf_counter() - run_start:.1f}s.")

    return status, games_scraped

def main():
    args = parse_args()
    log_file = setup_logging(args.log_level)
    pipeline_start = time.perf_counter()
    # Computed once so every year of this execution shares the same date in the bucket
    run_date = date.today()

    connection = create_connection()
    if connection is None:
        logger.error("Aborting pipeline: could not connect to the database.")
        return

    logger.info(f"Pipeline started for years {args.years}. Log file: {log_file}")

    with stage('create_tables'):
        create_tables()

    # Each year runs the whole pipeline before the next one starts
    results = {}
    try:
        for year in args.years:
            with stage(f'year {year}'):
                results[year] = run_year(connection, year, run_date)
    finally:
        connection.close()

    failed_years = [year for year, (status, _) in results.items() if status != 'success']
    total_games = sum(games for _, games in results.values())
    logger.info(f"Pipeline finished: {len(results) - len(failed_years)} years succeeded, failed years: {failed_years or 'none'}, {total_games} games in {time.perf_counter() - pipeline_start:.1f}s.")


if __name__ == "__main__":
    main()
