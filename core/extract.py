import requests
import time
import os
from tqdm import tqdm
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from core.parser import get_games

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
                print(f"Received status code {response.status_code}. Retrying in {delay} seconds...")
                time.sleep(delay * 2)
                continue

            response.raise_for_status()  # Raise an error for bad responses
            return response.text

        except requests.RequestException as e:
            print(f"Request failed: {e}.")
            time.sleep(delay)

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

def collect_game_list(years: list, dir_path: str = 'data/game_list') -> str:
    for y in years:
            year_url = f'https://www.metacritic.com/browse/game/all/all/{y}/metascore/?page='
            last_page_number = last_page(year_url) + 1
    
            for page in tqdm(range(1, last_page_number), desc="Fetching pages"):
                page_url = f'{year_url}{page}'
                page_content = fetch_page(page_url)
    
                if os.path.exists(dir_path):
                    with open(f'{dir_path}/y_{y}_pg_{page}.html', 'w', encoding='utf-8') as file:
                        file.write(page_content)
                else:
                    os.makedirs(dir_path, exist_ok=True)
                    with open(f'{dir_path}/y_{y}_pg_{page}.html', 'w', encoding='utf-8') as file:
                        file.write(page_content)

def list_game_links(dir_path: str = 'data/game_list') -> str:
    links = []
    if os.path.exists(dir_path):
        for file_name in os.listdir(dir_path):
            if file_name.endswith('.html'):
                with open(os.path.join(dir_path, file_name), 'r', encoding='utf-8') as file:
                    page_content = file.read()
                    game_links = get_games(page_content)
                    links.extend(game_links[1])
    else: print('Folder not found')
    return links

def collect_game_page(dir_path: str = 'data/game_pages') -> str:
    links = list_game_links()
    for link in tqdm(links, desc="Fetching game pages"):
        page_content = fetch_page(link)
        game_id = link.split('/')[-1]
        if os.path.exists(dir_path):
            with open(f'{dir_path}/{game_id}.html', 'w', encoding='utf-8') as file:
                file.write(page_content)
        else:
            os.makedirs(dir_path, exist_ok=True)
            with open(f'{dir_path}/{game_id}.html', 'w', encoding='utf-8') as file:
                file.write(page_content)