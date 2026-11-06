from pydantic import BaseModel
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

# Fields typed as `| None` are optional on Metacritic pages, so their database columns must accept NULL

class GameInfo(BaseModel):
    game_name: str
    released_date: date | None
    metascore_review: int | None
    user_review: int | None
    platforms: list[str]
    developer: str | None
    publisher: str | None
    genres: list[str]
    critic_positive: int | None
    critic_mixed: int | None
    critic_negative: int | None
    users_positive: int | None
    users_mixed: int | None
    users_negative: int | None
    must_play: bool
    description: str | None
    content_rating: str | None
    image_url: str | None

int_keys = [
    'metascore_review',
    'user_review',
    'critic_positive',
    'critic_mixed', 
    'critic_negative', 
    'users_positive', 
    'users_mixed', 
    'users_negative'
    ]

# Date formats found on game pages: ISO from the JSON-LD (1998-12-21) and the text shown in the details (Dec 21, 1998)
DATE_FORMATS = ['%Y-%m-%d', '%b %d, %Y']

# Convert the release date to a date, saving None when it is missing or not a date
def date_transform(data: dict) -> dict:

    if data['released_date'] is not None:
        text = data['released_date'].strip()
        data['released_date'] = None

        for date_format in DATE_FORMATS:
            try:
                data['released_date'] = datetime.strptime(text, date_format).date()
                break
            except ValueError:
                continue
        else:
            # Games without a defined release date show texts like 'TBA', which are stored as NULL
            logger.warning(f"Unrecognized release date {text!r}, saving it as None.")

    return data

# Convert string numbers to integers, handling None values
def number_transform_int(data: dict) -> dict:

    for key in int_keys:
        if data.get(key) is not None:
            value = str(data[key]).strip()
            try:
                if key == 'user_review':
                    # The user score goes from 0 to 10 with one decimal and is stored multiplied by 10 (8.8 -> 88, 10 -> 100)
                    data[key] = round(float(value) * 10)
                else:
                    # Counts use thousands separators (1,109 -> 1109)
                    data[key] = int(value.replace(',', '').replace('.', ''))
            except ValueError:
                raise ValueError(f"Invalid number format for {key}: {value!r}.")

    return data

# Clean the list of genres, handling None values (a game without genres gets an empty list)
def genre_transform(data: dict) -> dict:
    data['genres'] = [genre.strip() for genre in data.get('genres') or [] if genre and genre.strip()]
    return data

# Trim the free text fields and save None when they are empty (the description is not changed beyond that)
def text_transform(data: dict) -> dict:
    for key in ['description', 'content_rating', 'image_url']:
        value = data.get(key)
        data[key] = value.strip() or None if isinstance(value, str) else None
    return data

def data_normalization(data: dict) -> GameInfo:
    data = date_transform(data)
    data = number_transform_int(data)
    data = genre_transform(data)
    data = text_transform(data)
    return GameInfo(**data)