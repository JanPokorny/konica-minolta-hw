import imghdr
import logging
import pathlib
import typing

import backoff
import environ
import pika
import pika.exceptions

logging.basicConfig(level=logging.INFO)


@environ.config(prefix="")
class Config:
    IMAGE_FOLDER: pathlib.Path = environ.var(converter=pathlib.Path)
    ALLOWED_FORMATS: typing.Set[str] = environ.var(converter=lambda s: set(s.split(",")))
    RABBITMQ_HOST: str = environ.var()
    RABBITMQ_REQUEST_QUEUE: str = environ.var()
    WAIT_BETWEEN_SCANS_SEC: int = environ.var(converter=int)


def main() -> None:
    """
    Calls the loop_send_image_filenames function with arguments from the environment.
    """
    logging.info("Loader started")
    config = Config.from_environ()
    logging.info("Loaded configuration: %s", config)
    loop_send_image_filenames(
        image_folder=config.IMAGE_FOLDER,
        allowed_formats=config.ALLOWED_FORMATS,
        rabbitmq_host=config.RABBITMQ_HOST,
        rabbitmq_request_queue=config.RABBITMQ_REQUEST_QUEUE,
        wait_between_scans_sec=config.WAIT_BETWEEN_SCANS_SEC,
    )


@backoff.on_exception(backoff.expo, pika.exceptions.AMQPConnectionError, max_tries=10)
def loop_send_image_filenames(
        image_folder: pathlib.Path,
        allowed_formats: typing.Set[str],
        rabbitmq_host: str,
        rabbitmq_request_queue: str,
        wait_between_scans_sec: int
) -> None:
    """
    Repeatedly scans a folder for images and sends their filenames to a queue.

    :param image_folder: The folder to search for images.
    :param allowed_formats: The allowed image formats.
    :param rabbitmq_host: The hostname of the RabbitMQ server.
    :param rabbitmq_request_queue: The name of the queue to send the image filenames to.
    :param wait_between_scans_sec: The number of seconds to wait between each scan.
    """
    with pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host)) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_request_queue)
        logging.info("Connected to RabbitMQ")
        while True:
            logging.info("Sending a batch of images")
            send_image_filenames(image_folder, allowed_formats, channel, rabbitmq_request_queue)
            logging.info("Waiting for next scan (%d seconds)", wait_between_scans_sec)
            connection.sleep(wait_between_scans_sec)


def send_image_filenames(image_folder: pathlib.Path, allowed_formats: typing.Set[str],
                         channel: pika.adapters.blocking_connection.BlockingChannel, queue_name: str) -> None:
    """
    Scans a folder for images and sends their filenames to a queue.

    :param image_folder: The folder to search for images.
    :param allowed_formats: The allowed image formats.
    :param channel: The channel to send the image filenames to.
    :param queue_name: The name of the queue to send the image filenames to.
    """
    for image_filename in image_filenames(image_folder, allowed_formats):
        logging.info("Sending %s", image_filename)
        channel.basic_publish(exchange='', routing_key=queue_name, body=image_filename.encode('utf8'))


def image_filenames(image_folder: pathlib.Path, allowed_formats: typing.Set[str]) -> typing.Generator[str, None, None]:
    """
    Generate the filenames of images in a folder.

    :param image_folder: The folder to search for images.
    :param allowed_formats: The allowed image formats.
    :return: A generator of filenames of images in the folder.
    """
    for image_file in image_folder.iterdir():
        if is_image(image_file, allowed_formats):
            yield image_file.name
        else:
            logging.warning("Found non-image in input folder: %s", image_file.name)


def is_image(image_file: pathlib.Path, allowed_formats: typing.Set[str]) -> bool:
    """
    Check if the file is an image.

    :param image_file: The file to check.
    :param allowed_formats: The allowed image formats.
    :return: True if the file is an image, False otherwise.
    """
    return imghdr.what(image_file) in allowed_formats


if __name__ == '__main__':
    main()
