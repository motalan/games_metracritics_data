import requests
import time
from fake_useragent import UserAgent

# Set up a UserAgent instance to generate random user agents
ua = UserAgent()

def random_user_agent():
    #Generate a random user agent string.
    return ua.random

def fetch_page(url: str, retries=3, delay=2):
    # Fetch a web page with random user agent and retry mechanism.
    for i in range(retries):
        try:
            # Set up headers with a random user agent
            headers = {'User-Agent': random_user_agent()}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code in [403,429]:
                # If the response status code is 403 or 429, wait and retry
                print(f"Received status code {response.status_code}. Retrying in {delay} seconds...")
                time.sleep(delay * 2)
                continue

            response.raise_for_status()  # Raise an error for bad responses
            return response.text

        except requests.RequestException as e:
            print(f"Request failed: {e}.")
            time.sleep(delay)

    return None

def last_page(url:str) -> int:
    try:
        page = fetch_page(url)
        last_pages = page.find_all('span', class_='c-navigationPagination_itemButtonContent')
        last_page_number = last_pages[-2].text.strip()
    except:
        last_page_number = 1

    return int(last_page_number)
