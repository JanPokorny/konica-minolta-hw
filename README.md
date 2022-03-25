# Konica Minolta SW Developer (BE) homework

Solution for the pre-interview assignment for Back-End Developer position at Konica Minolta in Brno.

## Usage

There are sample input data attached in the `data/input` folder, courtesy of [Unsplash](https://unsplash.com/) photographers (credit in each file name).

Ensure you have Docker and Docker Compose installed and functional.

Then run, in the root of the project:

    docker-compose up

After the system starts up, you can observe that the images from `data/input` moved to `data/output/<color>`. To reset (return images back to the input folder), use `mv data/output/*/*.* data/input`.

## Technology

This project uses [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/overview/) to run a system of 4 microservices. (Using Kubernetes would be possible, but the YAMLs would be longer than the actual code.) The microservices all use the official [base Python image](https://hub.docker.com/_/python/) and run simple Python scripts communicating with each other using [RabbitMQ](https://www.rabbitmq.com/).

## Descriptions of the microservices

### RabbitMQ

A standard RabbitMQ instance is used for communication between the services.

### Loader

The assignment states that "The first module generates pictures for the system. Module picks up the pictures from the folder and pushes them to the system one by one.". This seems to imply that the service should send the whole image as a single message (and then presumably delete it), which is not a good idea since:

- RabbitMQ is not designed to handle large messages (it can handle up to 128 MB per message, but it is not recommended to congest it with raw data)
- The semantics of pushing the image to a queue and deleting it would create many points of failure where the image can be lost in transit
- Moving the image to a different location would require reading it into memory and then writing it to a different location, as opposed to simply moving the file within the filesystem

I decided to go with the sane option of sending just the image filename after some basic checks of input (eg. if it really is an image). In a real-world scenario, the image would be stored in some sort of object storage anyway.

### Detector

This service is responsible for detecting the color of the image. It uses [OpenCV](https://opencv.org/) and [NumPy](https://www.numpy.org/) to read the image and calculate the average color, then it uses a K-D tree from [SciPy](https://scipy.org/) (a bit overkill, but scalable!) to find the closest color in the named color list. HTML4 named colors were used, but the implementation is generic.

The detector responds to a message from the loader and then sends a message to the saver.

### Saver

Saver reacts to the message from the detector and saves the image to the output folder, to the appropriate color folder.

## Testing

To run tests, use the special Docker target `test`:

```
docker build services/loader --target test
docker build services/detector --target test
docker build services/saver --target test
```