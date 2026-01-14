import requests
from bs4 import BeautifulSoup
import pandas as pd



jogos = []

def request_page(year):
    link = f'https://www.metacritic.com/browse/game/all/all/{year}/metascore/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
    params = {'page':1}
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


