FROM python:3.9.13

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY Pipfile Pipfile.lock /code/
RUN pip install pipenv && pipenv install --system

# Required to run manage.py dbshell
RUN apt-get update
RUN apt-get --assume-yes install postgresql-client

COPY . /code/