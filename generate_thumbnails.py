import tempfile

from PIL import Image
from google.cloud import storage

THUMB_SIZE = 128, 128


def main(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    print(event)
    print(context)
    if event['contentType'].split('/')[0] != 'image':
        return
    client = storage.Client()
    bucket = client.get_bucket(event['bucket'])
    with tempfile.NamedTemporaryFile() as temp_image_file, tempfile.NamedTemporaryFile() as temp_thumb_file:
        get_image_file(event, temp_image_file.name, bucket)
        generate_thumbnail(temp_image_file.name, temp_thumb_file.name)
        bucket.blob(get_thumbnail_name(event['name'])).upload_from_filename(temp_thumb_file.name)


def get_thumbnail_name(image_name):
    return f"{image_name.split('.')[0]}_thumb.{image_name.split('.')[1]}"


def generate_thumbnail(image_file_name, thumbnail_file_name):
    image = Image.open(image_file_name)
    image.thumbnail(THUMB_SIZE)
    image.save(thumbnail_file_name, format='JPEG')


def get_image_file(event, destination_filename, bucket):
    blob = bucket.get_blob(event['name'])
    blob.download_to_filename(destination_filename)
