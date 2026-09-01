from core.extract import fetch_page, last_page
from tqdm import tqdm
from core.parser import get_games
import os

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


def main():
     pass

if __name__ == "__main__":
    main()
