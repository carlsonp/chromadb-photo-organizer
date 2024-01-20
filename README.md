# chromadb-photo-organizer

## Introduction

A photo similarity and organization tool leveraging the [chromadb](https://trychroma.com) vector database.

## Requirements

* Docker
* docker compose

## Installation and Setup

Copy `.env-copy` to `.env` and edit as needed

Add your images and photos to the `./images/` folder.

Bring up all the services via Docker

```shell
docker compose up -d --build
```

Access the web-ui: http://127.0.0.1:5000

## For Developers

Local development and testing

```shell
pip3 install --user chromadb open-clip-torch
export FLASK_APP=flaskapp
export FLASK_ENV=development
cd ./flask/
flask run --with-threads --debugger --host=0.0.0.0
```

Access the adminer page for connectivity to the Postgresql database backend.

http://127.0.0.1:8080

Then enter the following:

* System: `PostgreSQL`
* Server: `postgresql`
* Username: `root` <username set in `.env`>
* Password: `secret` <password set in `.env`>
* Database: `chromadb`

## References

* https://docs.trychroma.com/deployment
