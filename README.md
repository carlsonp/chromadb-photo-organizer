# chromadb-photo-organizer

## Introduction

A photo similarity and organization tool leveraging the [chromadb](https://trychroma.com) vector database.

## Requirements

* Docker
* docker compose

## Installation and Setup

Copy `.env-copy` to `.env` and edit as needed

Add your images and photos to the `./static/images/` folder.

Bring up all the services via Docker

```shell
docker compose up -d --build
```

Access the web-ui: http://127.0.0.1:5000

## For Developers

Local development and testing

```shell
docker compose -f docker-compose-dev.yml up -d --build
```

Use the `detox` utility to mass fix filenames, remove special characters, spaces, etc.

```shell
detox -r -v .
```

Extract the first frame from animated gifs

```shell
# find all unique file extensions
find . -type f -name '*.*' | sed 's|.*\.||' | sort -u
# adjust and convert the gifs
sudo apt install imagemagick
find . -type f -name "*.gif" -exec convert '{}[0]' {}.png \;
```

Cleanup files by extension

```shell
# for example .mp4 files
find . -type f -name '*.mp4' -exec rm -f {} \;
```

## References

* https://docs.trychroma.com/deployment
