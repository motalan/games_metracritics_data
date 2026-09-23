from pydantic import BaseModel
from datetime import date, datetime

class Platforms(BaseModel):
    platform_name: str

class Companies(BaseModel):
    company_name: str

class Genre(BaseModel):
    genre_name: str

class Game(BaseModel):
    game_name: str
    released_date: date
    summary: str

int_keys = [
    'metascore_review',
    'user_review',
    'positive_critic',
    'mixed_critic', 
    'negative_critic', 
    'positive_user', 
    'mixed_user', 
    'negative_user'
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

