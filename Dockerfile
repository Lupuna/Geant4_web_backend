FROM python:3.12-alpine3.20

COPY core /core
WORKDIR /core
EXPOSE 8001 5555

COPY requirements.txt /temp/requirements.txt
RUN pip install -r /temp/requirements.txt

RUN apk add postgresql-client build-base postgresql-dev
