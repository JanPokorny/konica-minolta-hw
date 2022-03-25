import logging
import pathlib

import backoff
import environ
import pika
import pika.exceptions

logging.basicConfig(level=logging.INFO)


@environ.config(prefix="")
class Config:
    IMAGE_FOLDER: pathlib.Path = environ.var(converter=pathlib.Path)
    OUTPUT_FOLDER: pathlib.Path = environ.var(converter=pathlib.Path)
    RABBITMQ_HOST: str = environ.var()
    RABBITMQ_RESPONSE_QUEUE: str = environ.var()


def main():
    """
    Calls the process_responses function with arguments from the environment.
    """
    logging.info("Detector started")
    config = Config.from_environ()
    logging.info("Loaded configuration: %s", config)
    process_responses(
        image_folder=config.IMAGE_FOLDER,
        output_folder=config.OUTPUT_FOLDER,
        rabbitmq_host=config.RABBITMQ_HOST,
        rabbitmq_response_queue=config.RABBITMQ_RESPONSE_QUEUE,
    )


@backoff.on_exception(backoff.expo, pika.exceptions.AMQPConnectionError, max_tries=10)
def process_responses(
        image_folder: pathlib.Path,
        output_folder: pathlib.Path,
        rabbitmq_host: str,
        rabbitmq_response_queue: str,
) -> None:
    """
    Processes the responses from the rabbitmq_response_queue.

    :param image_folder: The folder containing the images.
    :param output_folder: The folder to move the images to.
    :param rabbitmq_host: The host of the rabbitmq server.
    :param rabbitmq_response_queue: The queue to listen to.
    """
    with pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host)) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_response_queue)
        logging.info("Waiting for messages on %s", rabbitmq_response_queue)

        for method_frame, properties, body in channel.consume(rabbitmq_response_queue, auto_ack=True):  # type: ignore
            logging.info("Received message: %s", body)
            [color_name, filename] = body.decode('utf8').split('/', 1)
            logging.info("Moving file %s to output folder %s", filename, color_name)
            move_image(filename, color_name, image_folder, output_folder)


def move_image(
        filename: str,
        color_name: str,
        image_folder: pathlib.Path,
        output_folder: pathlib.Path,
) -> None:
    """
    Moves the image from the image_folder to the output_folder with the color_name as the sub-folder.

    :param filename: The filename of the image to move.
    :param color_name: The color name of the image.
    :param image_folder: The folder containing the image.
    :param output_folder: The folder to move the image to.
    """
    (output_folder / color_name).mkdir(parents=True, exist_ok=True)
    try:
        (image_folder / filename).rename(output_folder / color_name / filename)
    except FileNotFoundError:
        logging.error("File %s not found", filename)


if __name__ == '__main__':
    main()
