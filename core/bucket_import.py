import boto3
from botocore.config import Config
from dotenv import load_dotenv
import os

# Loading environment variables from .env file
load_dotenv()

def upload_files_to_s3(path_origin: str):

    # Create an S3 client using credentials from environment variables
    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("ENDPOINT_URL"),
        aws_access_key_id=os.getenv("RUSTFS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("RUSTFS_SECRET_KEY"),
        config=Config(s3={'addressing_style': 'path'})
    )

    BUCKET = "metacritic"
    
    # Iterate through files in the specified directory
    for file_name in os.listdir(path_origin):
        if file_name.endswith('.html'):
            # Upload each HTML file to the S3 bucket
            s3.upload_file(f'{path_origin}/{file_name}', BUCKET, f'game_pages/{file_name}')
            print(f"Uploaded {file_name} to S3 bucket {BUCKET}.")