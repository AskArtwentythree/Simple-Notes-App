FROM python:3.11-slim-buster AS base

WORKDIR /usr/src/app

COPY pyproject.toml .
COPY poetry.lock .
COPY app ./app

RUN pip install poetry
RUN poetry check
RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "-m", "app.main", "flask", "run"]