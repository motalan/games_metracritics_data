import boto3
from botocore.config import Config
from dotenv import load_dotenv
from datetime import date
from functools import lru_cache
import os
import logging

logger = logging.getLogger(__name__)

# Loading environment variables from .env file
load_dotenv()

BUCKET = "metacritic"

# Create the S3 client once, using credentials from environment variables
@lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("ENDPOINT_URL"),
        aws_access_key_id=os.getenv("RUSTFS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("RUSTFS_SECRET_KEY"),
        config=Config(s3={'addressing_style': 'path'})
    )

# Prefix where the pages of a release year are stored for a given execution date (e.g. runs/2026-11-05/2024/)
def run_prefix(run_date: date, year: int) -> str:
    return f'runs/{run_date.isoformat()}/{year}/'

# Upload an HTML page kept in memory to the bucket (an existing key is overwritten)
def upload_content(key: str, content: str):
    get_s3_client().put_object(
        Bucket=BUCKET,
        Key=key,
        Body=content.encode('utf-8'),
        ContentType='text/html; charset=utf-8'
    )
    logger.debug(f"Uploaded s3://{BUCKET}/{key}.")

# List every key under a prefix ending with the given suffix (S3 returns at most 1000 keys per call, so it paginates)
def list_files(prefix: str, suffix: str = '.html') -> list[str]:
    paginator = get_s3_client().get_paginator('list_objects_v2')

    keys = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        keys.extend(obj['Key'] for obj in page.get('Contents', []) if obj['Key'].endswith(suffix))

    return sorted(keys)

# Read a file from the bucket and return its content as text
def read_file(key: str) -> str:
    response = get_s3_client().get_object(Bucket=BUCKET, Key=key)
    return response['Body'].read().decode('utf-8')

def upload_files_to_s3(path_origin: str, run_id: int):
    s3 = get_s3_client()
    uploaded = 0

    # Iterate through files in the specified directory
    for file_name in os.listdir(path_origin):
        if file_name.endswith('.html'):
            # Upload each HTML file to the S3 bucket, under the prefix of its scrape run
            s3.upload_file(f'{path_origin}/{file_name}', BUCKET, f'runs/{run_id}/game_pages/{file_name}')
            logger.debug(f"Uploaded {file_name} to S3 bucket {BUCKET}.")
            uploaded += 1

    logger.info(f"Uploaded {uploaded} files to s3://{BUCKET}/runs/{run_id}/game_pages/.")

    return uploaded
