# ziklive backend

ZikLive is a platform that empowers artists and promoters to centralize and manage their events calendar.  
Artists can easily publish their concert schedules, allowing fans to follow their favorite performers and book tickets.  

Beyond event management, ZikLive enables live streaming and post-event replays — giving artists and promoters new opportunities to **monetize performances and replays**.  

The ZikLive backend is built using Django, PostgreSQL, and Redis (with Docker for local development).
For the MVP for the Demo, Mux, a managed service, was selected to provide live streaming capabilities through OBS/RTMP and WebRTC (browser).

---

This project can power a scalable, real time supporting:
- Live concert broadcasts in high quality via `Mux streaming`
- Automated `ticket sales and payment processing`
- Multi-role access for `artists`, `fans`, and `promoters`
- Secure and performant infrastructure with `Redis caching` and `PostgreSQL`


---


## Ressources

- [Django secret in container](https://stackoverflow.com/questions/48549983/how-do-i-make-django-secrets-available-inside-docker-containers)
- [Django installation](https://www.djangoproject.com/download/)
- [Django tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)
- [Django create app / startapp](https://www.w3schools.com/django/django_create_app.php)
- [Django Rest Framework](https://www.django-rest-framework.org/)
- [Django cloudinary storage](https://cloudinary.com/documentation/django_helper_methods_tutorial)
- [Cloudinary documentation](https://cloudinary.com/documentation/django_integration)
- [Stripe api](https://docs.stripe.com/api/metadata)
- [Mux python](https://github.com/muxinc/mux-python)

---

## Tech Stack

| Component | Description |
|------------|-------------|
| **Framework** | Django 5 + Django REST Framework |
| **Authentication** | JWT (SimpleJWT) + Redis-based session management |
| **Database** | PostgreSQL |
| **Cache / Queues** | Redis |
| **Media Storage** | Cloudinary (banners, images, media files) |
| **Live Streaming** | Mux API (OBS / WebRTC) |
| **Payments** | Stripe |
| **Testing** | Pytest, pytest-django, pytest-cov |
| **Containerization** | Docker & docker-compose (test local) |
| **Language** | Python3 |


---

## Project Structure

- [`ziklive_backend/`](ziklive_backend/) – Core Django settings, URLs, and WSGI configuration  
- [`users/`](users/) – User management, roles, and JWT authentication  
- [`artists/`](artists/) – Artist and promoter profiles  
- [`events/`](events/) – Event creation, scheduling, and media banners  
- [`tickets/`](tickets/) – Ticket purchasing and reservation logic  
- [`streaming/`](streaming/) – Mux live streaming integration (RTMP / WebRTC)  
- [`docker/`](docker/) – Docker configuration files  
- [`tests/`](tests/) – Unit and integration test suites  
- [`requirements.txt`](requirements.txt) – Python dependencies  
- [`docker-compose.yml`](docker-compose.yml) – Service orchestration  
- [`manage.py`](manage.py) – Django management script  

---


## ⚙️ Installation & Setup

### Create and activate a virtual environment

```
python -m venv venv
```
#### On Windows
zikenv\Scripts\activate

#### On Ubuntu
source venv/bin/activate

#### Deactivate
```deactivate```

### Install dependencies

```pip install -r requirements.txt
```



## INSTALL POSTGRESQL ON UBUNTU:

```
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo service postgresql start

```

### Show the superuser on db:
```
\du
```
Or:
```
SELECT * FROM pg_roles;
```
### To enter in the POSTGRESQL SHELL

```
sudo -u postgres psql
CREATE DATABASE db_name;
ALTER USER postgres WITH PASSWORD 'db_password';
```

#### list of db:
```
\l
```
#### Show db:
```
\c db_name
```

#### Show infos in the table user:
SELECT * FROM users_user;

### Exit db
`Ctrl + D`


### Migrate
```
python manage.py makemigrations
python manage.py migrate
```
### Create superuser
```
python manage.py createsuperuser
```

### Start backend
```
python manage.py runserver
```

### Show tables:
```
\dt
```


## INSTALL REDIS 
#### In Ubuntu
```
sudo apt update
sudo apt install redis-server

(oWe can do also: sudo apt install redis-server -y; 
-y = yes default)

```

### test fonctionnality redis
```
sudo service redis-server start      OR    sudo systemctl start redis-server
sudo service redis-server status     OR    sudo systemctl status redis-server
sudo service redis-server stop       OR    sudo systemctl stop redis-server
sudo service redis-server restart    OR    sudo systemctl restart redis-server

```


### Show logs
```
journalctl -u redis-server
```


- Start redis auto on boot:
```
sudo systemctl enable redis-server
```


### Deactive redis automaticaly on boot:
```
sudo systemctl disable redis-server
```



- Test redis connection, output PONG:
```
redis-cli ping
```


### CONNEXION REDIS SHELL
```redis-cli```


#### List of keys:
KEYS *


## Build and run with Docker:
```
sudo systemctl start docker
docker-compose build
docker-compose up
```

## Licence
Copyright ZikLive 2025 - All right reserved
