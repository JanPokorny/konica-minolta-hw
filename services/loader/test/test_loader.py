import pathlib
from unittest.mock import MagicMock, call

from pika.adapters.blocking_connection import BlockingChannel

import loader

IMAGE_FOLDER = pathlib.Path(__file__).parent / "data"
ALLOWED_FORMATS = {"bmp", "jpeg", "png", "tiff", "gif", "webp"}


def test_is_image():
    allowed_formats = {file.suffix[1:] for file in IMAGE_FOLDER.iterdir()}
    for file in IMAGE_FOLDER.iterdir():
        assert loader.is_image(file, allowed_formats) == (file.suffix[1:] in ALLOWED_FORMATS)


def test_image_filenames():
    generated_filenames = loader.image_filenames(IMAGE_FOLDER, ALLOWED_FORMATS)
    assert {filename.split(".")[1] for filename in generated_filenames} == ALLOWED_FORMATS


def test_send_image_filenames():
    channel = MagicMock(spec=BlockingChannel)
    queue_name = 'test_queue_name'

    loader.send_image_filenames(
        image_folder=IMAGE_FOLDER,
        allowed_formats=ALLOWED_FORMATS,
        channel=channel,
        queue_name=queue_name
    )

    assert channel.basic_publish.has_calls(
        [call(exchange='', routing_key=queue_name, body=f"sample.{ext}".encode('utf8')) for ext in ALLOWED_FORMATS],
        any_order=True
    )

