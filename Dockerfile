FROM python:3.11-slim-buster AS base

WORKDIR /usr/src/app

COPY .streamlit ./.streamlit
COPY pyproject.toml .
COPY poetry.lock .
COPY app ./app

RUN pip install poetry \
 && poetry check \
 && poetry install --no-root

EXPOSE 8080 8501

ENV DEEP_TRANSLATE_API_KEY=""


CMD sh -c "\
    poetry run python -m app.main flask run --host=0.0.0.0 --port=8080 & \
    poetry run streamlit run app/frontend.py --server.address=0.0.0.0 --server.port=8501 \
"
