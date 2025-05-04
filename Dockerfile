FROM python:3.11-slim-buster AS base

WORKDIR /usr/src/app

COPY pyproject.toml .
COPY poetry.lock .
COPY app ./app

RUN --mount=type=secret,id=deep_tranlate_api_key,env=DEEP_TRANSLATE_API_KEY
RUN pip install poetry
RUN poetry install

CMD ["poetry", "run", "python", "-m", "app.main"]