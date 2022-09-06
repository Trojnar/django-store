# Django-Store
Simple store in python django.

## Setup project
To set up this project locally: 
* Set up variables.env file located in the main project directory, then move the file to ./config/environment/ path.
* Set up environment using docker containers.

```
$ docker-compose up --build
```
* Migrate database.
```
$ docker-compose exec web python manage.py migrate
```

* Create superuser.
```
$ docker-compose exec web python manage.py createsuperuser
```
