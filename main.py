from core.extract import fetch_page, last_page
from tqdm import tqdm
import os

def main():

    for year in range(2025,2026):
        year_url = f'https://www.metacritic.com/browse/game/all/all/{year}/metascore/?page='
        last_page_number = last_page(year_url)

        for page in tqdm(range(1, last_page_number + 1), desc="Fetching pages"):
            page_url = f'{year_url}{page}'
            page_content = fetch_page(page_url)

            if os.path.exists(f'data/{year}/game_list'):
                with open(f'data/{year}/game_list/page_{page}.html', 'w', encoding='utf-8') as file:
                    file.write(page_content)
            else:
                os.makedirs(f'data/{year}/game_list', exist_ok=True)
                with open(f'data/{year}/game_list/page_{page}.html', 'w', encoding='utf-8') as file:
                    file.write(page_content)


if __name__ == "__main__":
    main()
