from bs4 import BeautifulSoup


def souping (text_page: str) -> BeautifulSoup:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(text_page, 'html.parser')
    return soup

def last_page(text_page: str) -> int:

    soup = souping(text_page)

    # Try to find the last page number from the pagination elements
    try:            
        last_pages = soup.find_all('span', class_='c-navigationPagination_itemButtonContent')
        last_page_number = last_pages[-2].text.strip()
    except: 
        last_page_number = 1

    return int(last_page_number)

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