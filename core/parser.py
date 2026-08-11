from bs4 import BeautifulSoup

# Souping function to parse HTML content
def souping (text_page: str) -> BeautifulSoup:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(text_page, 'html.parser')
    return soup

# Function to extract game's name and links from the HTML content
def get_games(text_page: str) -> list:
    soup = souping(text_page)

    games = []
    link_games = []

    # Find all game titles and links on the page
    lista = soup.find_all('h3', class_='c-finderProductCard_titleHeading')
    links = soup.find_all('a', class_='c-finderProductCard_container g-color-gray80 u-grid')

    for i in lista:
        games.append(i.text.split('.', 1)[1].strip())

    for i in links:
        link_games.append(i.get('href'))

    return games, link_games

# Function to extract detailed information about a specific game from the HTML content
def get_game_info(text_page: str) -> list:
    soup = souping(text_page)

    # Basic information about the game that is available for all game's page
    game_name = soup.find('h1').text    
    platforms = soup.find_all('li', class_='c-gameDetails_listItem g-color-gray70 u-inline-block')
    platforms = [games.text.strip() for games in platforms]
    genres = soup.find_all('span', class_='c-globalButton_label')[-2].text.strip()

    # Additional information about the game handling cases where certain elements may not be present
    try:
        released_date = soup.find_all('div', class_='g-text-xsmall')[1].find_all('span')[-1].text
    except:
        released_date = None

    try:
        developer = soup.find('li', class_='c-gameDetails_listItem u-inline-block g-color-gray70').text.strip()
    except:
        developer = soup.find_all('a', class_='u-text-underline')[-2].text.strip()
    try:
       publisher = soup.find('span', class_='g-outer-spacing-left-medium-fluid u-block g-color-gray70').text.strip()
    except:
        publisher = soup.find_all('a', class_='u-text-underline')[-1].text.strip()
    
    try:
        metascore_review = soup.find('div', class_='c-siteReviewScore_medium').text
        positive_critic = soup.find('div', class_='c-reviewsStats_positiveStats').find_all('span')[-1].text.split(' ')[0]
        mixed_critic = soup.find('div', class_='c-reviewsStats_neutralStats').find_all('span')[-1].text.split(' ')[0]
        negative_critic = soup.find('div', class_='c-reviewsStats_negativeStats').find_all('span')[-1].text.split(' ')[0]
    except:
        positive_critic = None
        mixed_critic = None
        negative_critic = None
        metascore_review = None
    try:
        user_review = soup.find_all('div', class_='c-siteReviewScore_medium')[1].find('span').text
        positive_user = soup.find_all('div', class_='c-reviewsStats_positiveStats')[2].find_all('span')[-1].text.split(' ')[0]
        mixed_user = soup.find_all('div', class_='c-reviewsStats_neutralStats')[2].find_all('span')[-1].text.split(' ')[0]
        negative_user = soup.find_all('div', class_='c-reviewsStats_negativeStats')[2].find_all('span')[-1].text.split(' ')[0]
    except:
        positive_user = None
        mixed_user = None
        negative_user = None
        user_review = None

    # Create a dictionary to store the extracted game information
    data = {'game_name': game_name,
            'released_date': released_date,
            'metascore_review': metascore_review,
            'user_review': user_review,
            'platforms': platforms,
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