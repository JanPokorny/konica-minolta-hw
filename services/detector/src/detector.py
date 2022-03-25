import logging
import pathlib

import backoff
import cv2
import environ
import numpy as np
import pika
import pika.exceptions

from color_namer import guess_color_name

logging.basicConfig(level=logging.INFO)


@environ.config(prefix="")
class Config:
    IMAGE_FOLDER: pathlib.Path = environ.var(converter=pathlib.Path)
    RABBITMQ_HOST: str = environ.var()
    RABBITMQ_REQUEST_QUEUE: str = environ.var()
    RABBITMQ_RESPONSE_QUEUE: str = environ.var()


def main():
    """
    Calls the respond_to_image_query function with arguments from the environment.
    """
    logging.info("Detector started")
    config = Config.from_environ()
    logging.info("Loaded configuration: %s", config)
    respond_to_image_query(
        image_folder=config.IMAGE_FOLDER,
        rabbitmq_host=config.RABBITMQ_HOST,
        rabbitmq_request_queue=config.RABBITMQ_REQUEST_QUEUE,
        rabbitmq_response_queue=config.RABBITMQ_RESPONSE_QUEUE,
    )


@backoff.on_exception(backoff.expo, pika.exceptions.AMQPConnectionError, max_tries=10)
def respond_to_image_query(
        image_folder: pathlib.Path,
        rabbitmq_host: str,
        rabbitmq_request_queue: str,
        rabbitmq_response_queue: str,
):
    """
    Responds to image queries by sending the color name of the image.

    :param image_folder:
    :param rabbitmq_host:
    :param rabbitmq_request_queue:
    :param rabbitmq_response_queue:
    :return:
    """
    with pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host)) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_request_queue)
        channel.queue_declare(queue=rabbitmq_response_queue)
        logging.info("Waiting for messages on %s", rabbitmq_request_queue)

        for method_frame, properties, body in channel.consume(rabbitmq_request_queue, auto_ack=True):  # type: ignore
            logging.info("Received message: %s", body)
            filename = body.decode('utf8')
            color_name = guess_image_color(image_folder / filename)
            logging.info("Detected color %s for image %s", color_name, filename)
            response = f"{color_name}/{filename}"
            channel.basic_publish(
                exchange='',
                routing_key=rabbitmq_response_queue,
                body=response.encode('utf8')
            )


def guess_image_color(image_path: pathlib.Path) -> str:
    """
    Guesses the color of an image.

    :param image_path: Path to the image
    :return: Color name
    """
    image = load_image(image_path)
    avg_color = average_color(image)
    return guess_color_name(avg_color)


def load_image(image_path: pathlib.Path) -> np.ndarray:
    """
    Loads an image from a path.

    :param image_path: Path to the image
    :return: Image data as numpy array of shape M x N x 3
    """
    try:
        return cv2.cvtColor(cv2.imread(str(image_path)), cv2.COLOR_BGR2RGB)
    except cv2.error:
        logging.error("Failed to load image %s", image_path)


def average_color(image: np.ndarray) -> np.ndarray:
    """
    Calculates the average color of an image.

    :param image: Image data as numpy array of shape M x N x 3
    :return: RGB color as numpy array of shape 3
    """
    if len(image.shape) != 3 or image.shape[-1] != 3:
        raise ValueError("Image array must be of shape M x N x 3")
    return np.mean(image, axis=(0, 1))


if __name__ == '__main__':
    main()
