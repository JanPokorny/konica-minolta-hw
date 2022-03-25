import pathlib
from unittest.mock import MagicMock, call

import pytest
import detector
import numpy as np


IMAGE_FOLDER = pathlib.Path(__file__).parent / "data"


def test_respond_to_image_query(mocker):
    mocked_blocking_connection = MagicMock()
    mocker.patch("detector.pika.BlockingConnection", mocked_blocking_connection)
    mocked_blocking_connection.return_value.__enter__.return_value.channel.return_value.consume.return_value = [
        (None, None, b"black_pixel.png"),
        (None, None, b"white_pixel.png")
    ]

    detector.respond_to_image_query(
        image_folder=IMAGE_FOLDER,
        rabbitmq_host="fake.host",
        rabbitmq_request_queue="fake_request_queue",
        rabbitmq_response_queue="fake_response_queue",
    )

    assert mocked_blocking_connection.return_value.channel.return_value.publish.has_calls([
        call(
            exchange='',
            routing_key="fake_response_queue",
            body=b"black/black_pixel.png"
        ),
        call(
            exchange='',
            routing_key="fake_response_queue",
            body=b"white/white_pixel.png"
        )
    ])


def test_guess_image_color():
    assert detector.guess_image_color(IMAGE_FOLDER / "black_pixel.png") == "black"
    assert detector.guess_image_color(IMAGE_FOLDER / "white_pixel.png") == "white"


def test_load_image():
    assert (detector.load_image(IMAGE_FOLDER / "black_pixel.png") == np.array([[[0, 0, 0]]])).all()
    assert (detector.load_image(IMAGE_FOLDER / "white_pixel.png") == np.array([[[255, 255, 255]]])).all()


def test_average_color():
    assert (detector.average_color(np.array([[[0, 0, 0], [0, 0, 0]]])) == np.array([0, 0, 0])).all()
    assert (detector.average_color(np.array([[[255, 255, 255], [255, 255, 255]]])) == np.array([255, 255, 255])).all()
    assert (detector.average_color(np.array([[[100, 0, 0], [0, 100, 0]]])) == np.array([50, 50, 0])).all()
    with pytest.raises(ValueError):
        detector.average_color(np.array([0, 0, 0]))
