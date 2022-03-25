from unittest.mock import MagicMock

import saver


def test_process_responses(mocker, tmp_path):
    TEST_IN_FOLDER = tmp_path / "in"
    TEST_OUT_FOLDER = tmp_path / "out"

    TEST_IN_FOLDER.mkdir(exist_ok=True)
    TEST_OUT_FOLDER.mkdir(exist_ok=True)

    (TEST_IN_FOLDER / "fire.png").touch()
    (TEST_IN_FOLDER / "water.png").touch()

    mocked_blocking_connection = MagicMock()
    mocker.patch("saver.pika.BlockingConnection", mocked_blocking_connection)
    mocked_blocking_connection.return_value.__enter__.return_value.channel.return_value.consume.return_value = [
        (None, None, b"red/fire.png"),
        (None, None, b"blue/water.png")
    ]

    saver.process_responses(
        image_folder=TEST_IN_FOLDER,
        output_folder=TEST_OUT_FOLDER,
        rabbitmq_host="fake.host",
        rabbitmq_response_queue="fake_response_queue",
    )

    assert (TEST_OUT_FOLDER / "red" / "fire.png").exists()
    assert (TEST_OUT_FOLDER / "blue" / "water.png").exists()


def test_move_image(tmp_path):
    TEST_FILENAME = "test.png"
    TEST_COLOR_NAME = "test_color"
    TEST_IN_FOLDER = tmp_path / "in"
    TEST_OUT_FOLDER = tmp_path / "out"

    TEST_IN_FOLDER.mkdir(exist_ok=True)
    TEST_OUT_FOLDER.mkdir(exist_ok=True)

    TEST_FILE_PATH = TEST_IN_FOLDER / TEST_FILENAME
    TEST_FILE_PATH.touch()

    saver.move_image(
        filename=TEST_FILENAME,
        color_name=TEST_COLOR_NAME,
        image_folder=TEST_IN_FOLDER,
        output_folder=TEST_OUT_FOLDER,
    )

    assert (TEST_OUT_FOLDER / TEST_COLOR_NAME / TEST_FILENAME).exists()
