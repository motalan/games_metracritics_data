import requests
from bs4 import BeautifulSoup
import pandas as pd

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
params = {'page':1}

def request_page(year:int):
    link = f'https://www.metacritic.com/browse/game/all/all/{year}/metascore/'
    request = requests.get(link,headers=headers,params=params)
    page = BeautifulSoup(request.text, 'html.parser')
    return page


def get_last_page(year: int):
    try:
        page = request_page(year)
        last_pages = page.find_all('span', class_='c-navigationPagination_itemButtonContent')
        last_page_number = last_pages[-2].text.strip()
    except:
        last_page_number = 1
    return int(last_page_number)

def get_games(year: int):
    games = []
    link_games = []
    last_page = get_last_page(year)
    while params['page'] <= last_page:
        page = request_page(year)
        page.find_all('h3', class_='c-finderProductCard_titleHeading')

        lista = page.find_all('h3', class_='c-finderProductCard_titleHeading')
        links = page.find_all('a', class_='c-finderProductCard_container g-color-gray80 u-grid')
    
        for i in lista:
            games.append(i.text.split('.',1)[1].strip())

        for i in links:
            link_games.append(i.get('href'))
        
        if last_page == 1:
            break
        params['page'] += 1
    
    return pd.DataFrame({'Game': games, 'Link': link_games})

get_games(2026).to_csv('data/raw/games_2026.csv',index=False)