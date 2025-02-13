install:
	poetry install

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

dev:
	poetry run flask --app page_analyzer:app --debug run 

build:
	./build.sh

mypy:
	poetry run mypy page_analyzer/db.py
	poetry run mypy page_analyzer/app.py
	poetry run mypy page_analyzer/html.py
	poetry run mypy page_analyzer/validators.py

lint:
	poetry run flake8 page_analyzer