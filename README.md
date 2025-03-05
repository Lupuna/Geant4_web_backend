# Geant4 WebBackend

**Geant4 WebBackend** — это один из микросервисов проекта **Geant4**.  
Микросервис разработан с использованием **Django Rest Framework**.

## Используемые технологии

- **Docker**
- **Celery**
- **Django Rest Framework**
- **Nginx**
- **PostgreSQL**
- **Redis**
- **RabbitMQ**

## Описание

Данный микросервис служит посредником между пользователем и **Geant4**.  
В рамках микросервиса реализовано:

- Взаимодействие пользователя с примерами  
- Файловая система  
- Личный кабинет пользователя  
- Администрирование приложения  

Микросервис построен на принципе **контейнеризации**.  
Каждый компонент запускается в отдельном **Docker-контейнере**:

- Веб-приложение (Django)
- База данных (**PostgreSQL**)
- **Redis**
- Веб-сервер (**Nginx**)

Сборка и управление контейнерами осуществляются через **Docker Compose**.  
Файлы сборки находятся в `docker-compose.prod.yml` и **Dockerfile** (для веб-сервера есть дополнительный Dockerfile, см. структуру проекта).  
Также реализован полный **CI/CD цикл**.

## Структура проекта
.github/ 
  └── workflows/ 
        └── core.yml 
core/ 
  ├── api/ 
       └── v1/ 
  ├── core/ 
  ├── file_client/ 
  ├── geant_examples/ 
  ├── geant_tests_storage/ 
  ├── users/ 
  ├── logs/ 
  ├── tests/ 
  ├── celery_app.py 
  └── manage.py 
nginx/ 
  └── nginx.conf 
docker-compose.prod.yml 
Dockerfile 
requirements.txt