import requests
from bs4 import BeautifulSoup
import pandas as pd

link = 'https://www.metacritic.com/game/clair-obscur-expedition-33/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
params = {'page':1}

page = requests.get(link,params=params,headers=headers)
page = BeautifulSoup(page.text,'html.parser')
metascore_review = page.find('div', class_='c-siteReviewScore u-flexbox-column u-flexbox-alignCenter u-flexbox-justifyCenter g-text-bold c-siteReviewScore_green g-color-gray90 c-siteReviewScore_medium').text
user_review = page.find('div', class_='c-siteReviewScore u-flexbox-column u-flexbox-alignCenter u-flexbox-justifyCenter g-text-bold c-siteReviewScore_green c-siteReviewScore_user g-color-gray90 c-siteReviewScore_medium').text
platforms = page.find_all('li', class_='c-gameDetails_listItem g-color-gray70 u-inline-block')
platforms = [games.text.strip() for games in platforms]
developer = page.find('li', class_='c-gameDetails_listItem u-inline-block g-color-gray70').text
