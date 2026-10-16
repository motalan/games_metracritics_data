import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Create a database connection
def create_connection():

    try:
        connection = psycopg2.connect(
            host = os.getenv("HOST"),
            port = os.getenv("PORT"),
            database = os.getenv("DATABASE"),
            user = os.getenv("USERNAME"),
            password = os.getenv("PASSWORD")
        )
        return connection
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# Create tables and constraints in the database
def create_tables():
    connection = create_connection()
    cursor = connection.cursor()

    # Create the platforms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform (
            platform_id SERIAL PRIMARY KEY,
            platform_name VARCHAR(255) NOT NULL
        );
        ''')

    # Create the genres table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS genre (
            genre_id SERIAL PRIMARY KEY,
            genre_name VARCHAR(255) NOT NULL
        );
    ''')

    # Create the companies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company (
            company_id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL
            );
        ''')

    # Create the games table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game (
            game_id SERIAL PRIMARY KEY,
            game_name VARCHAR(255) NOT NULL,
            released_date DATE,
            must_play BOOLEAN NOT NULL
    );
    '''
    )

    # Create the critic reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS critic_reviews (
            review_id SERIAL PRIMARY KEY,
            game_id INT REFERENCES game (game_id),
            metascore_review INT NOT NULL,
            critic_positive INT NOT NULL,
            critic_mixed INT NOT NULL,
            critic_negative INT NOT NULL
        );
    ''')

    # Create the users reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_reviews (
            review_id SERIAL PRIMARY KEY,
            game_id INT REFERENCES game (game_id),
            users_overall_score INT NOT NULL,
            users_positive INT NOT NULL,
            users_mixed INT NOT NULL,
            users_negative INT NOT NULL
        );
    ''')

    # Create the game_platforms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_platforms (
            game_id INT REFERENCES game (game_id),
            platform_id INT REFERENCES platform (platform_id),
            PRIMARY KEY (game_id, platform_id)
        );
    ''')

    # Create the game_genres table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_genres (
            game_id INT REFERENCES game (game_id),
            genre_id INT REFERENCES genre (genre_id),
            PRIMARY KEY (game_id, genre_id)
        );
    ''')

    # Create the game_companies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_companies (
            game_id INT REFERENCES game (game_id),
            company_id INT REFERENCES company (company_id),
            bond_type VARCHAR(255) NOT NULL,
            PRIMARY KEY (game_id, company_id)
        );
    ''')

    # Commit the changes and close the connection
    connection.commit()
    cursor.close()
    connection.close()

# Insert data into the specified table
def insert_data(table_name: str, data: dict):
    connection = create_connection()

    cursor = connection.cursor()

    # Prepare the SQL statement for inserting data
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING *;"
    cursor.execute(sql, list(data.values()))

    # Commit the changes and close the connection
    connection.commit()
    cursor.close()
    connection.close()

    return cursor.fetchone()  # Return the inserted row

create_tables()  # Create tables when the module is imported