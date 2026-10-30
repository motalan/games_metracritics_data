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

# Find a product details section by its label (e.g. 'Platforms:')
def product_details_section(soup: BeautifulSoup, label: str):
    for section in soup.find_all('div', class_='c-product-details__section'):
        section_label = section.find('span', class_='c-product-details__section__label')
        if section_label is not None and section_label.text.strip() == label:
            return section
    return None

# Function to extract detailed information about a specific game from the HTML content
def get_game_info(text_page: str) -> list:
    soup = souping(text_page)

    # Basic information about the game that is available for all game's page
    game_name = soup.find('h1').text    
    # The publisher section uses the same list item class, so only the platforms section is read
    platforms_section = product_details_section(soup, 'Platforms:')
    platforms = [item.text.strip() for item in platforms_section.find_all('li', class_='c-product-details__section__list-item')] if platforms_section else []
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

    # Create a dictionary to store the extracted game information
    data = {'game_name': game_name,
            'released_date': released_date,
            'metascore_review': metascore_review,
            'user_review': user_review,
            'platforms': platforms,
            'developer': developer,
            'publisher': publisher,
            'genres': genres,
            'critic_positive': positive_critic,
            'critic_mixed': mixed_critic,
            'critic_negative': negative_critic,
            'users_positive': positive_user,
            'users_mixed': mixed_user,
            'users_negative': negative_user,
            'must_play': must_play
            }
    
    return data
