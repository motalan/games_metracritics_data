import psycopg2
from dotenv import load_dotenv
import os
from core.transform import GameInfo

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

    # Create the scrape runs table (one row per scraping execution)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrape_run (
            run_id SERIAL PRIMARY KEY,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ,
            status VARCHAR(20) NOT NULL DEFAULT 'running',
            years INT[],
            s3_prefix VARCHAR(255),
            games_scraped INT DEFAULT 0
        );
    ''')

    # Create the platforms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform (
            platform_id SERIAL PRIMARY KEY,
            platform_name VARCHAR(255) NOT NULL UNIQUE
        );
        ''')

    # Create the genres table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS genre (
            genre_id SERIAL PRIMARY KEY,
            genre_name VARCHAR(255) NOT NULL UNIQUE
        );
    ''')

    # Create the companies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company (
            company_id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL UNIQUE
            );
        ''')

    # Create the games table (game_slug is the metacritic link, e.g. /game/elden-ring/)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game (
            game_id SERIAL PRIMARY KEY,
            game_slug VARCHAR(255) NOT NULL UNIQUE,
            game_name VARCHAR(255) NOT NULL,
            released_date DATE,
            first_seen_run_id INT REFERENCES scrape_run (run_id)
    );
    '''
    )

    # Create the critic reviews table (one snapshot per game per scrape run)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS critic_reviews (
            review_id SERIAL PRIMARY KEY,
            run_id INT NOT NULL REFERENCES scrape_run (run_id),
            game_id INT NOT NULL REFERENCES game (game_id),
            collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            metascore_review INT,
            critic_positive INT,
            critic_mixed INT,
            critic_negative INT,
            must_play BOOLEAN NOT NULL,
            UNIQUE (game_id, run_id)
        );
    ''')

    # Create the users reviews table (one snapshot per game per scrape run)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_reviews (
            review_id SERIAL PRIMARY KEY,
            run_id INT NOT NULL REFERENCES scrape_run (run_id),
            game_id INT NOT NULL REFERENCES game (game_id),
            collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            users_overall_score INT,
            users_positive INT,
            users_mixed INT,
            users_negative INT,
            UNIQUE (game_id, run_id)
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
            PRIMARY KEY (game_id, company_id, bond_type)
        );
    ''')

    # Create views with the most recent snapshot of each game
    cursor.execute('''
        CREATE OR REPLACE VIEW latest_critic_reviews AS
        SELECT DISTINCT ON (game_id) *
        FROM critic_reviews
        ORDER BY game_id, collected_at DESC;
    ''')

    cursor.execute('''
        CREATE OR REPLACE VIEW latest_users_reviews AS
        SELECT DISTINCT ON (game_id) *
        FROM users_reviews
        ORDER BY game_id, collected_at DESC;
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
    inserted_row = cursor.fetchone()

    # Commit the changes and close the connection
    connection.commit()
    cursor.close()
    connection.close()

    return inserted_row  # Return the inserted row

# Register a new scrape run and return its id
def start_run(connection, years: list) -> int:
    cursor = connection.cursor()

    cursor.execute("INSERT INTO scrape_run (years) VALUES (%s) RETURNING run_id;", (years,))
    run_id = cursor.fetchone()[0]

    # Raw HTML of this run is stored under its own prefix in the S3 bucket
    cursor.execute("UPDATE scrape_run SET s3_prefix = %s WHERE run_id = %s;", (f'runs/{run_id}/', run_id))

    connection.commit()
    cursor.close()

    return run_id

# Close a scrape run with its final status (success | failed)
def finish_run(connection, run_id: int, status: str, games_scraped: int):
    cursor = connection.cursor()

    cursor.execute('''
        UPDATE scrape_run
        SET finished_at = now(), status = %s, games_scraped = %s
        WHERE run_id = %s;
    ''', (status, games_scraped, run_id))

    connection.commit()
    cursor.close()

# Insert a value into a lookup table (platform, genre, company) if it doesn't exist and return its id
def get_or_create(connection, table_name: str, value: str) -> int:
    cursor = connection.cursor()

    # DO UPDATE (instead of DO NOTHING) makes RETURNING also work when the row already exists
    sql = f'''
        INSERT INTO {table_name} ({table_name}_name) VALUES (%s)
        ON CONFLICT ({table_name}_name) DO UPDATE SET {table_name}_name = EXCLUDED.{table_name}_name
        RETURNING {table_name}_id;
    '''
    cursor.execute(sql, (value,))
    row_id = cursor.fetchone()[0]

    cursor.close()

    return row_id

# Insert or update a game and its platforms, genres and companies, returning the game id
def upsert_game(connection, game: GameInfo, game_slug: str, run_id: int) -> int:
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO game (game_slug, game_name, released_date, first_seen_run_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (game_slug) DO UPDATE
        SET game_name = EXCLUDED.game_name, released_date = EXCLUDED.released_date
        RETURNING game_id;
    ''', (game_slug, game.game_name, game.released_date, run_id))
    game_id = cursor.fetchone()[0]

    for platform in game.platforms:
        platform_id = get_or_create(connection, 'platform', platform)
        cursor.execute('''
            INSERT INTO game_platforms (game_id, platform_id) VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        ''', (game_id, platform_id))

    for genre in game.genres:
        genre_id = get_or_create(connection, 'genre', genre)
        cursor.execute('''
            INSERT INTO game_genres (game_id, genre_id) VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        ''', (game_id, genre_id))

    for bond_type, company in [('developer', game.developer), ('publisher', game.publisher)]:
        company_id = get_or_create(connection, 'company', company)
        cursor.execute('''
            INSERT INTO game_companies (game_id, company_id, bond_type) VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
        ''', (game_id, company_id, bond_type))

    connection.commit()
    cursor.close()

    return game_id

# Save the critic and users reviews of a game as a snapshot of the given scrape run
def save_snapshot(connection, run_id: int, game_id: int, game: GameInfo):
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO critic_reviews (run_id, game_id, metascore_review, critic_positive, critic_mixed, critic_negative, must_play)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (game_id, run_id) DO NOTHING;
    ''', (run_id, game_id, game.metascore_review, game.critic_positive, game.critic_mixed, game.critic_negative, game.must_play))

    cursor.execute('''
        INSERT INTO users_reviews (run_id, game_id, users_overall_score, users_positive, users_mixed, users_negative)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (game_id, run_id) DO NOTHING;
    ''', (run_id, game_id, game.user_review, game.users_positive, game.users_mixed, game.users_negative))

    connection.commit()
    cursor.close()
