black:
	black ./src --line-length=120

isort:
	isort ./src --profile black

update_reqs:
	pip-compile requirements.in

build:
	docker-compose build

run:
	docker-compose up -d
