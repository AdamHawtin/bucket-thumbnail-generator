import os
import tempfile
from pathlib import Path

from PIL import Image
from google.cloud import storage
from retrying import retry

THUMBNAIL_SIZE = int(os.getenv('THUMBNAIL_SIZE', '128'))
THUMBNAIL_MAX_DIM = THUMBNAIL_SIZE, THUMBNAIL_SIZE
THUMBNAIL_SUFFIX = f'_thumb{THUMBNAIL_SIZE}'
SUPPORTED_FILE_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def receive_event(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file_extension = Path(event['name']).suffix.lstrip('.')
    if not is_event_supported_image(event, file_extension):
        return
    print(event, context)
    bucket = storage.Client().get_bucket(event['bucket'])
    with tempfile.NamedTemporaryFile() as temp_image_file, tempfile.NamedTemporaryFile() as temp_thumb_file:
        get_image_file(event, temp_image_file, bucket)
        image_format = generate_and_save_thumbnail(temp_image_file.name, temp_thumb_file.name)
        upload_thumbnail_to_bucket(bucket, temp_thumb_file, get_thumbnail_name(event['name'], file_extension),
                                   image_format)


def is_file_extension_supported(file_extension):
    return file_extension.lower() in SUPPORTED_FILE_EXTENSIONS


def is_event_supported_image(event, file_extension):
    return (event['contentType'].startswith('image') and
            THUMBNAIL_SUFFIX not in event['name'] and
            is_file_extension_supported(file_extension))


def get_thumbnail_name(image_name, file_extension):
    return f'{Path(image_name).stem}{THUMBNAIL_SUFFIX}.{file_extension}'


def generate_and_save_thumbnail(image_file_name, thumbnail_file_name):
    image = Image.open(image_file_name)
    image_format = image.format
    image.thumbnail(THUMBNAIL_MAX_DIM, Image.ANTIALIAS)
    image.save(thumbnail_file_name, format=image_format)
    return image_format


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def upload_thumbnail_to_bucket(bucket, temp_thumb_file, thumbnail_filename, image_format):
    bucket.blob(thumbnail_filename).upload_from_filename(temp_thumb_file.name,
                                                         content_type=f'image/{image_format.lower()}')


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def get_image_file(event, destination_file, bucket):
    blob = bucket.get_blob(event['name'])
    blob.download_to_file(destination_file)
