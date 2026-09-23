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
    lista = soup.find_all('h3', class_='m-0 text-base leading-5.5 font-bold lg:overflow-hidden lg:text-ellipsis lg:line-clamp-1 lg:max-h-5.5 lg:wrap-break-word')
    links = soup.find_all('a', class_='grid grid-cols-[5.5rem_auto] gap-x-1 gap-y-1 md:gap-x-4 text-gray-800 no-underline')

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
    platforms = soup.find_all('li', class_='c-product-details__section__list-item')
    platforms = [games.text.strip() for games in platforms]
    genres = soup.find_all('span', class_='global-link-button__label')[-2].text.strip()

    # Additional information about the game handling cases where certain elements may not be present
    try:
        released_date = soup.find_all('div', class_='c-product-details__section c-product-details__section--grouped')[1].find_all('span')[-1].text
    except:
        released_date = None
    try:
        developer = soup.find('a', class_='text-gray-800 underline').text.strip()
    except:
        developer = soup.find_all('div', class_='flex flex-col items-stretch gap-2 pt-8 max-lg:pt-0')[0].find_all('span')[-1].text
    try:
       publisher = soup.find_all('a', class_='c-product-detail-link')[-1].text.strip()
    except:
        publisher = soup.find_all('div', class_='c-product-details__section c-product-details__section--grouped')[-1].find_all('span')[-1].text
    
    try:
        metascore_review = soup.find('div', class_='flex flex-col items-center gap-1 self-start').text
        positive_critic = soup.find('div', class_='reviews-stats__positive-stats').find_all('span')[-1].text.split(' ')[0]
        mixed_critic = soup.find('div', class_='reviews-stats__neutral-stats').find_all('span')[-1].text.split(' ')[0]
        negative_critic = soup.find('div', class_='reviews-stats__negative-stats').find_all('span')[-1].text.split(' ')[0]
    except:
        positive_critic = None
        mixed_critic = None
        negative_critic = None
        metascore_review = None
    try:
        user_review = soup.find_all('div', class_='flex flex-col items-center gap-1 self-start')[1].find('span').text
        positive_user = soup.find_all('div', class_='reviews-stats__positive-stats')[1].find_all('span')[-1].text.split(' ')[0]
        mixed_user = soup.find_all('div', class_='reviews-stats__neutral-stats')[1].find_all('span')[-1].text.split(' ')[0]
        negative_user = soup.find_all('div', class_='reviews-stats__negative-stats')[1].find_all('span')[-1].text.split(' ')[0]
    except:
        positive_user = None
        mixed_user = None
        negative_user = None
        user_review = None

    # Must play is a boolean value that indicates whether the game is considered a "must play" title based on the presence of a specific HTML element
    if soup.find('div', class_='size-12 md:size-13 shrink-0') is not None:
        must_play = 1
    else:
        must_play = 0

    # Summary is a brief description of the game, extracted from a specific HTML element if it exists
    if soup.find('div', class_='text-base leading-[1.75rem] text-gray-900 max-md:leading-4') is not None:
        summary = soup.find('div', class_='text-base leading-[1.75rem] text-gray-900 max-md:leading-4').text
    else:
        summary = None


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
            'negative_user': negative_user,
            'must_play': must_play,
            'summary': summary
            }
    
    return data
