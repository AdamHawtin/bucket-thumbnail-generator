import os
import tempfile
from pathlib import Path

from PIL import Image
from google.cloud import storage
from retrying import retry

THUMBNAIL_SIZE = int(os.getenv('THUMBNAIL_SIZE', '128'))
THUMBNAIL_MAX_DIM = THUMBNAIL_SIZE, THUMBNAIL_SIZE
THUMBNAIL_SUFFIX = f'_thumb{THUMBNAIL_SIZE}'


def main(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    if not event['contentType'].startswith('image') or THUMBNAIL_SUFFIX in event['name']:
        # Ignore non-images and thumbnails
        return
    print(event)
    print(context)
    client = storage.Client()
    bucket = client.get_bucket(event['bucket'])
    with tempfile.NamedTemporaryFile() as temp_image_file, tempfile.NamedTemporaryFile() as temp_thumb_file:
        get_image_file(event, temp_image_file.name, bucket)
        image_format = generate_thumbnail(temp_image_file.name, temp_thumb_file.name)
        upload_thumbnail_to_bucket(bucket, temp_thumb_file, get_thumbnail_name(event['name'], image_format))


def get_thumbnail_name(image_name, image_format):
    return f'{Path(image_name).stem}{THUMBNAIL_SUFFIX}.{image_format}'


def generate_thumbnail(image_file_name, thumbnail_file_name):
    image = Image.open(image_file_name)
    image_format = image.format
    image.thumbnail(THUMBNAIL_MAX_DIM, Image.ANTIALIAS)
    image.save(thumbnail_file_name, format=image_format)
    return image_format


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def upload_thumbnail_to_bucket(bucket, temp_thumb_file, thumbnail_filename):
    bucket.blob(thumbnail_filename).upload_from_filename(temp_thumb_file.name, content_type='image/jpeg')


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def get_image_file(event, destination_filename, bucket):
    blob = bucket.get_blob(event['name'])
    blob.download_to_filename(destination_filename)
