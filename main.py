import argparse
import logging
import os
import time
from contextlib import contextmanager
from datetime import date, datetime
from tqdm import tqdm
from dotenv import load_dotenv
from core.extract import collect_game_list, collect_game_page
from core.parser import get_game_info
from core.transform import data_normalization
from core.bucket_import import upload_files_to_s3
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

def count_html(dir_path: str) -> int:
    return len([file_name for file_name in os.listdir(dir_path) if file_name.endswith('.html')])

# Parse every game page of the run and save it in the database, returning how many games were saved
def load_games(connection, run_id: int, dir_pages: str) -> int:
    saved = 0
    failed = 0

    files = sorted(file_name for file_name in os.listdir(dir_pages) if file_name.endswith('.html'))

    for file_name in tqdm(files, desc="Loading games"):
        # Game pages are saved by slug (elden-ring.html -> /game/elden-ring/)
        game_slug = f'/game/{file_name.removesuffix(".html")}/'

        try:
            with open(os.path.join(dir_pages, file_name), 'r', encoding='utf-8') as file:
                game = data_normalization(get_game_info(file.read()))

            game_id = upsert_game(connection, game, game_slug, run_id)
            save_snapshot(connection, run_id, game_id, game)
            saved += 1
            logger.debug(f"Saved {game_slug} (game_id={game_id}).")

        except Exception:
            # A page with an unexpected layout must not stop the whole run
            connection.rollback()
            failed += 1
            logger.exception(f"Failed to load {file_name}.")

    logger.info(f"{saved} games saved, {failed} failed.")

    return saved

def main():
    args = parse_args()
    log_file = setup_logging(args.log_level)
    pipeline_start = time.perf_counter()

    connection = create_connection()
    if connection is None:
        logger.error("Aborting pipeline: could not connect to the database.")
        return

    with stage('create_tables'):
        create_tables()

    run_id = start_run(connection, args.years)
    logger.info(f"Scrape run {run_id} started for years {args.years}. Log file: {log_file}")

    # Each run keeps its own HTML so old pages are not uploaded or saved again
    dir_list = f'data/runs/{run_id}/game_list'
    dir_pages = f'data/runs/{run_id}/game_pages'
    os.makedirs(dir_list, exist_ok=True)
    os.makedirs(dir_pages, exist_ok=True)

    status = 'failed'
    games_scraped = 0

    try:
        with stage('collect_game_list'):
            collect_game_list(args.years, dir_list)
        logger.info(f"{count_html(dir_list)} list pages saved in {dir_list}.")

        with stage('collect_game_page'):
            collect_game_page(dir_pages, dir_list)
        logger.info(f"{count_html(dir_pages)} game pages saved in {dir_pages}.")

        with stage('upload_files_to_s3'):
            upload_files_to_s3(dir_pages, run_id)

        with stage('load_games'):
            games_scraped = load_games(connection, run_id, dir_pages)

        status = 'success'

    except Exception:
        logger.exception(f"Scrape run {run_id} failed.")
        raise

    finally:
        connection.rollback()  # Discard any transaction left open by a failure
        finish_run(connection, run_id, status, games_scraped)
        connection.close()
        logger.info(f"Scrape run {run_id} finished with status '{status}': {games_scraped} games in {time.perf_counter() - pipeline_start:.1f}s.")


if __name__ == "__main__":
    main()
