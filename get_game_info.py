import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
params = {'page':1}
game_data = []

def request_page(link: str):
    base_link = 'https://www.metacritic.com'
    page = requests.get((base_link+link),params=params,headers=headers)
    page = BeautifulSoup(page.text,'html.parser')
    return page

def game_info(page):

    game_name = page.find('h1').text
    released_date = page.find_all('div', class_='g-text-xsmall')[1].find_all('span')[-1].text
    platforms = page.find_all('li', class_='c-gameDetails_listItem g-color-gray70 u-inline-block')
    platforms = [games.text.strip() for games in platforms]
    genres = page.find_all('span', class_='c-globalButton_label')[-2].text.strip()
    try:
        developer = page.find('li', class_='c-gameDetails_listItem u-inline-block g-color-gray70').text.strip()
    except:
        developer = page.find_all('a', class_='u-text-underline')[-2].text.strip()
    try:
       publisher = page.find('span', class_='g-outer-spacing-left-medium-fluid u-block g-color-gray70').text.strip()
    except:
        publisher = page.find_all('a', class_='u-text-underline')[-1].text.strip()
    
    try:
        metascore_review = page.find('div', class_='c-siteReviewScore_medium').text
        positive_critic = page.find('div', class_='c-reviewsStats_positiveStats').find_all('span')[-1].text.split(' ')[0]
        mixed_critic = page.find('div', class_='c-reviewsStats_neutralStats').find_all('span')[-1].text.split(' ')[0]
        negative_critic = page.find('div', class_='c-reviewsStats_negativeStats').find_all('span')[-1].text.split(' ')[0]
    except:
        positive_critic = None
        mixed_critic = None
        negative_critic = None
        metascore_review = None
    try:
        user_review = page.find_all('div', class_='c-siteReviewScore_medium')[1].find('span').text
        positive_user = page.find_all('div', class_='c-reviewsStats_positiveStats')[2].find_all('span')[-1].text.split(' ')[0]
        mixed_user = page.find_all('div', class_='c-reviewsStats_neutralStats')[2].find_all('span')[-1].text.split(' ')[0]
        negative_user = page.find_all('div', class_='c-reviewsStats_negativeStats')[2].find_all('span')[-1].text.split(' ')[0]
    except:
        positive_user = None
        mixed_user = None
        negative_user = None
        user_review = None

    data = {'game_name': game_name,
            'relesade_date': released_date,
            'metascore_review': metascore_review,
            'user_review': user_review,
            'plataforms': platforms,
            'developer': developer,
            'publisher': publisher,
            'genres': genres,
            'positive_critic': positive_critic,
            'mixed_critic': mixed_critic,
            'negative_critic': negative_critic,
            'positive_user': positive_user,
            'mixed_user': mixed_user,
            'negative_user': negative_user
            }
    
    return data

dataframe = pd.read_csv('data/raw/game_year/games_2024.csv')

for game in dataframe['Link'].values:
    page = request_page(game)
    game_data.append(game_info(page))

with open('data/raw/game_info/game_info_2024.json', 'w', encoding='utf-8') as file:
    json.dump(game_data ,file,indent=4)