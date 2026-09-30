from pydantic import BaseModel
from datetime import date, datetime

class GameInfo(BaseModel):
    game_name: str
    released_date: date
    metascore_review: int
    user_review: int
    platforms: list[str]
    developer: str
    publisher: str
    genres: list[str]
    critic_positive: int
    critic_mixed: int
    critic_negative: int
    users_positive: int
    users_mixed: int
    users_negative: int
    must_play: bool

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

# Validator function to ensure the date is in the correct format
def date_transform(data: dict) -> dict:

    if data['released_date'] is not None:

        try:
            converted_date = datetime.strptime(data['released_date'].strip(), '%b %d, %Y').date()
            data['released_date'] = converted_date
        except ValueError:
            raise ValueError("Invalid date format. Please use the format 'Mon DD, YYYY'.")

    return data

# Convert string numbers to integers, handling None values
def number_transform_int(data: dict) -> dict:

    for key in int_keys:
        if data.get(key) is not None:
            try:
                data[key] = int(data[key].replace('.', '').strip())  # Remove periods and whitespace before converting to int
            except ValueError:
                raise ValueError(f"Invalid number format for {key}. Please ensure it's a valid integer.")

    return data

# Convert string to list of genres, handling None values
def genre_transform(data: dict) -> dict:
    if data['genres'] is not None:
        data['genres'] = [genre.replace("-", " ") for genre in data['genres'].split(' ')]
    return data

def data_normalization(data: dict) -> GameInfo:
    data = date_transform(data)
    data = number_transform_int(data)
    data = genre_transform(data)
    return GameInfo(**data)