import requests
from bs4 import BeautifulSoup
import pandas as pd

link = 'https://www.metacritic.com/game/the-legend-of-zelda-tears-of-the-kingdom-nintendo/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
params = {'page':1}

page = requests.get(link,params=params,headers=headers)
page = BeautifulSoup(page.text,'html.parser')
released_date = page.find_all('div', class_='g-text-xsmall')[1].find_all('span')[-1].text
metascore_review = page.find('div', class_='c-siteReviewScore u-flexbox-column u-flexbox-alignCenter u-flexbox-justifyCenter g-text-bold c-siteReviewScore_green g-color-gray90 c-siteReviewScore_medium').text
user_review = page.find('div', class_='c-siteReviewScore u-flexbox-column u-flexbox-alignCenter u-flexbox-justifyCenter g-text-bold c-siteReviewScore_green c-siteReviewScore_user g-color-gray90 c-siteReviewScore_medium').text
platforms = page.find_all('li', class_='c-gameDetails_listItem g-color-gray70 u-inline-block')
platforms = [games.text.strip() for games in platforms]
#developer = page.find('li', class_='c-gameDetails_listItem u-inline-block g-color-gray70').text
#publisher = page.find('span', class_='g-outer-spacing-left-medium-fluid u-block g-color-gray70').text
genres = page.find_all('span', class_='c-globalButton_label')[-2].text.strip().split(" ")
postive_critic = page.find('div', class_='c-reviewsStats_positiveStats').find_all('span')[-1].text.split(" ")[0]
mixed_critic = page.find('div', class_='c-reviewsStats_neutralStats').find_all('span')[-1].text.split(" ")[0]
negative_critic = page.find('div', class_='c-reviewsStats_negativeStats').find_all('span')[-1].text.split(" ")[0]
positive_user = page.find_all('div', class_='c-reviewsStats_positiveStats')[2].find_all('span')[-1].text.split(" ")[0]
mixed_user = page.find_all('div', class_='c-reviewsStats_neutralStats')[2].find_all('span')[-1].text.split(" ")[0]
negative_user = page.find_all('div', class_='c-reviewsStats_negativeStats')[2].find_all('span')[-1].text.split(" ")[0]
print(released_date)