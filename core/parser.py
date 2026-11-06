import json
import re
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

# Read the schema.org VideoGame object that the game page embeds as JSON-LD ({} when it is missing or invalid)
def json_ld(soup: BeautifulSoup) -> dict:
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get('@type') == 'VideoGame':
            return data
    return {}

# Read the values of a block in the game details section by its label (e.g. 'Platforms:')
def detail_values(soup: BeautifulSoup, label: str) -> list[str]:
    details = soup.find(attrs={'data-testid': 'game-details'})
    if details is None:
        return []

    for span in details.find_all('span'):
        if span.get_text(strip=True) == label:
            block = span.parent
            values = [item.get_text(strip=True) for item in block.find_all('li')]
            values += [item.get_text(strip=True) for item in block.find_all('span', class_='c-product-details__section__value')]
            return [value for value in values if value]
    return []

# Read the score and the positive, mixed and negative counts of the critic-reviews or user-reviews section
def score_section(soup: BeautifulSoup, testid: str) -> tuple:
    section = soup.find(attrs={'data-testid': testid})
    if section is None:
        return None, None, None, None

    # The score is 'tbd' while there are not enough reviews
    score_tag = section.find(attrs={'data-testid': 'global-score-value'})
    score = score_tag.get_text(strip=True) if score_tag else None
    if score is None or not re.fullmatch(r'\d+(\.\d+)?', score):
        score = None

    # Counts are shown as '88% Positive | 976 Ratings' (or 'Reviews' for critics)
    text = section.get_text(' | ', strip=True)
    counts = []
    for sentiment in ['Positive', 'Mixed', 'Negative']:
        match = re.search(rf'{sentiment} \| ([\d,]+) (?:Reviews?|Ratings?)', text)
        counts.append(match.group(1) if match else None)

    return score, *counts

# Read the developer shown below the game summary (a link or plain text after the 'Developer:' label)
def developer_name(soup: BeautifulSoup) -> str | None:
    block = soup.find(attrs={'data-testid': 'hero-summary-developer'})
    if block is None:
        return None

    for tag in block.find_all(['a', 'span']):
        name = tag.get_text(strip=True)
        if name and name != 'Developer:':
            return name
    return None

# Function to extract detailed information about a specific game from the HTML content
# The JSON-LD is the main source because it does not depend on CSS classes, and the details section is the fallback
def get_game_info(text_page: str) -> dict:
    soup = souping(text_page)
    ld = json_ld(soup)

    title = soup.find('h1')
    game_name = ld.get('name') or (title.get_text(strip=True) if title else None)

    released_date = ld.get('datePublished') or next(iter(detail_values(soup, 'Initial Release Date:')), None)

    platforms = ld.get('gamePlatform') or detail_values(soup, 'Platforms:')
    if isinstance(platforms, str):
        platforms = [platforms]

    genres = ld.get('genre') or detail_values(soup, 'Genres:')
    if isinstance(genres, str):
        genres = [genres]

    # Only the first publisher is kept
    publishers = ld.get('publisher') or []
    if isinstance(publishers, dict):
        publishers = [publishers]
    publisher_names = [item.get('name') for item in publishers if isinstance(item, dict) and item.get('name')]
    publisher = next(iter(publisher_names or detail_values(soup, 'Publisher:')), None)

    developer = developer_name(soup)

    # These fields only exist in the JSON-LD (None when the page does not have them)
    description = ld.get('description')
    content_rating = ld.get('contentRating')

    # The image is normally a URL, but it could also be a list or an object with the url
    image = ld.get('image')
    if isinstance(image, list):
        image = image[0] if image else None
    if isinstance(image, dict):
        image = image.get('url')

    metascore_review, positive_critic, mixed_critic, negative_critic = score_section(soup, 'critic-reviews')
    user_review, positive_user, mixed_user, negative_user = score_section(soup, 'user-reviews')

    # Must play is true when the score badge shows the must-play image
    must_play = soup.select_one('[data-testid="global-score-badge"] img[alt="must-play"]') is not None

    # Create a dictionary to store the extracted game information (None or [] when the page does not have it)
    data = {'game_name': game_name,
            'released_date': released_date,
            'metascore_review': metascore_review,
            'user_review': user_review,
            'platforms': platforms or [],
            'developer': developer,
            'publisher': publisher,
            'genres': genres or [],
            'critic_positive': positive_critic,
            'critic_mixed': mixed_critic,
            'critic_negative': negative_critic,
            'users_positive': positive_user,
            'users_mixed': mixed_user,
            'users_negative': negative_user,
            'must_play': must_play,
            'description': description,
            'content_rating': content_rating,
            'image_url': image
            }

    return data
