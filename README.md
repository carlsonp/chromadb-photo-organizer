# chromadb-photo-organizer

## Introduction

A photo similarity and organization tool leveraging the [chromadb](https://trychroma.com) vector database.

## Requirements

* Docker (with buildkit enabled, see `/etc/docker/daemon.json`)
* docker compose

## Features

* Search your images using descriptive words such as "beach holiday" or "sunset".
* Browse your images and find similar images quickly
* Favorite and upvote images you like
* Optionally cleanup file names
* Extract images from animated files and videos (GIF, WEBM, MP4...)
* Supports PNG, JPG, GIF, WEBM, MP4 files

## Installation and Setup

Copy `.env-copy` to `.env` and edit as needed

Add your images and photos to the `./static/images/` folder.  **Always** keep a backup of your images!

Generate a public cert and private key pair for Traefik.  For example:

```shell
cd ./traefik/
openssl req -x509 -nodes -days 4096 -newkey rsa:2048 -out cert.crt -keyout cert.key -subj "/C=US/ST=Self/L=Self/O=Self/CN=192.168.1.112" -addext "subjectAltName = IP:192.168.1.112"
```

Or use Let's Encrypt or some other method.

Edit the `./traefik/traefik.yaml` file and adjust the *.crt and *.key names as needed.

Edit `docker-compose.yml` and adjut the Traefik IP address or hostname

Bring up all the services via Docker

```shell
docker compose up -d --build
```

Access the web-ui: `https://<your IP or hostname>:8448` via your browser.
You may need to accept the cert if it's self-signed.

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

Cleanup and delete files by extension

```shell
# for example .mp4 files
find . -type f -name '*.mp4' -exec rm -f {} \;
```

## References

* https://docs.trychroma.com/deployment
