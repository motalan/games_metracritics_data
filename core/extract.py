import requests
import time
import logging
from tqdm import tqdm
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from core.parser import get_games
from core.bucket_import import upload_content, list_files, read_file

logger = logging.getLogger(__name__)

# Set up a UserAgent instance to generate random user agents
ua = UserAgent()

def random_user_agent():
    #Generate a random user agent string.
    return str(ua.random)

def fetch_page(url: str, retries=3, delay=2):
    # Fetch a web page with random user agent and retry mechanism.
    for i in range(retries):
        try:
            # Set up headers with a random user agent
            headers = {'User-Agent': random_user_agent()}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code in [403,429]:
                # If the response status code is 403 or 429, wait and retry
                logger.warning(f"Received status code {response.status_code} for {url}. Retrying in {delay * 2} seconds...")
                time.sleep(delay * 2)
                continue

            response.raise_for_status()  # Raise an error for bad responses
            return response.text

        except requests.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}.")
            time.sleep(delay)

    logger.error(f"Giving up on {url} after {retries} retries.")
    return None

def last_page(url:str) -> int:
    try:
        page = fetch_page(url)
        soup = BeautifulSoup(page, 'html.parser')
        last_pages = soup.find_all('span', class_='c-navigation-pagination__item-content')
        last_page_number = last_pages[-2].text.strip()
    except:
        last_page_number = 1

    return int(last_page_number)

# Download every list page of a release year and save it in the bucket, returning how many pages were saved
def collect_game_list(year: int, prefix: str) -> int:
    year_url = f'https://www.metacritic.com/browse/game/all/all/{year}/metascore/?page='
    last_page_number = last_page(year_url) + 1
    saved = 0

    for page in tqdm(range(1, last_page_number), desc="Fetching pages"):
        page_content = fetch_page(f'{year_url}{page}')
        if page_content is None:
            logger.error(f"Skipping list page {page} of {year}: page could not be fetched.")
            continue

        upload_content(f'{prefix}game_list/y_{year}_pg_{page}.html', page_content)
        saved += 1

    return saved

# Read the list pages from the bucket, download each game page and save it in the bucket, returning how many pages were saved
def collect_game_page(prefix: str) -> int:
    base_url = 'https://www.metacritic.com'
    saved = 0

    for list_key in list_files(f'{prefix}game_list/'):
        games, links = get_games(read_file(list_key))

        for game, link in tqdm(list(zip(games, links)), desc="Fetching game pages"):
            page_content = fetch_page(base_url + link)
            if page_content is None:
                logger.error(f"Skipping {game}: page could not be fetched.")
                continue

            # Save the page by its slug to keep the link to the game
            slug = link.strip('/').split('/')[-1]
            upload_content(f'{prefix}game_pages/{slug}.html', page_content)
            saved += 1

    return saved
