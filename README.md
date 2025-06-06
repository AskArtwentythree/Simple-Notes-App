﻿# Simple-Notes-App

The **Simple-Notes-App** is a simple, secure web-based application that allows users to create, edit, delete, and translate personal notes from Russian to English language. It provides a clean Streamlit frontend, a Flask API backend, and stores data in a local SQLite database. 

## Features:

- JWT-based user authentication (Sign up / Sign in);
- Full note management: create, read, update, delete, save;
- Built-in translation from Russian to English via Deep Translate API;
- Persistent storage with SQLite;

## Getting Started:

To run the app locally with Docker:

```bash
docker build -t notes_app .
docker run --rm -it \
  -e DEEP_TRANSLATE_API_KEY=<your_deep_translate_api_key> \
  -p 8080:8080 -p 8501:8501 notes_app
```

The backend API will be available at http://localhost:8080, and the Streamlit frontend at http://localhost:8501:
![](images/image_2025-05-08_23-26-45.png)

## Tech Stack:

- Python (Flask, Streamlit, pytest)
- SQLite3
- JWT authentication
- bcrypt for password hashing
- Deep Translate API
- Docker

## Quality Goals:

- 90%+ test pass rate and 60%+ code coverage
- PEP8-compliant, Flake8-clean code
- Maintainability Index > 70
- Secure storage & API response practices
