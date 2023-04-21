black:
	black ./src --line-length=120

isort:
	isort ./src --profile black

update_reqs:
	pip-compile requirements.in

build:
	# builds the containers
	docker-compose build

run:
	# runs the local server in docker & sets up all databases
	docker-compose up -d

setup:
	# sets up the local environment for development
	bash setup.sh
