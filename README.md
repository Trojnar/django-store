# Django-Store
Simple store in python django.

## Setup project
To set up this project locally: 
* Set up variable.env file in main project directory, then move the file to ./config/environment/ path.
* Then, set up environment using docker containers.

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
