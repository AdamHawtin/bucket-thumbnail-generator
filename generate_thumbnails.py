import os
import tempfile
from pathlib import Path

from PIL import Image
from google.cloud import storage

THUMBNAIL_SIZE = int(os.getenv('THUMBNAIL_SIZE', '128'))
THUMBNAIL_MAX_DIM = THUMBNAIL_SIZE, THUMBNAIL_SIZE
THUMBNAIL_SUFFIX = f'_thumb{THUMBNAIL_SIZE}.jpg'


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
        generate_thumbnail(temp_image_file.name, temp_thumb_file.name)
        bucket.blob(get_thumbnail_name(event['name'])).upload_from_filename(temp_thumb_file.name, content_type='image/jpeg')


def get_thumbnail_name(image_name):
    return f'{Path(image_name).stem}{THUMBNAIL_SUFFIX}'


def generate_thumbnail(image_file_name, thumbnail_file_name):
    image = Image.open(image_file_name)
    image.thumbnail(THUMBNAIL_MAX_DIM)
    image.save(thumbnail_file_name, format='JPEG')


def get_image_file(event, destination_filename, bucket):
    blob = bucket.get_blob(event['name'])
    blob.download_to_filename(destination_filename)
