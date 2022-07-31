FROM python:3.9.13

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

# Required to run manage.py dbshell, and memcache
RUN apt-get update
RUN apt-get --assume-yes install postgresql-client
RUN apt-get --assume-yes install libmemcached-dev

COPY Pipfile Pipfile.lock /code/
RUN pip install pipenv && pipenv install --system



COPY . /code/
