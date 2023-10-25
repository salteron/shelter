PROJECT_NAME := shelter
RUN := run --rm
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.yml -f docker-compose.dev.yml
DOCKER_COMPOSE_RUN := ${DOCKER_COMPOSE} $(RUN)

default: test

install:
	poetry install

test:
	pytest ${PROJECT_NAME}/

test-and-coverage:
	pytest ${PROJECT_NAME}/ --cov-report term:skip-covered --cov-report html --cov ${PROJECT_NAME} --cov-config .coveragerc

lint:
	flake8 ${PROJECT_NAME}/

types:
	mypy ${PROJECT_NAME}/

migrate:
	./manage.py migrate

check-migrations:
	./manage.py makemigrations --check --dry-run

compose-build:
	${DOCKER_COMPOSE} build web

compose-bash:
	${DOCKER_COMPOSE_RUN} web bash

compose-install:
	${DOCKER_COMPOSE_RUN} app make install

compose-migrate:
	${DOCKER_COMPOSE_RUN} app make migrate

compose-down:
	${DOCKER_COMPOSE} down

compose-web:
	${DOCKER_COMPOSE_RUN} --service-ports web

compose-psql:
	${DOCKER_COMPOSE_RUN} db psql -h db -U postgres ${DB}

compose-prepare: compose-build compose-install compose-migrate

compose-test:
	${DOCKER_COMPOSE_RUN} app make test
