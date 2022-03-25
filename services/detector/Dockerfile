# syntax=docker/dockerfile:1

FROM python:3.10 as base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY src src
COPY test test
RUN pytest

FROM base as deploy
COPY src src
ENTRYPOINT ["python", "-u", "src/detector.py"]
