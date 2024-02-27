FROM ubuntu:22.04

# https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/reference.md#run---mounttypecache
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt install -y --no-install-recommends nano ca-certificates python3 python3-pip python3-flask curl detox imagemagick && \
    apt -y upgrade && \
    apt autoremove -y

# https://docs.docker.com/build/guide/mounts/#add-a-cache-mount
RUN --mount=type=cache,target=/root/.cache/pip pip3 install --user chromadb open-clip-torch gunicorn flask-compress

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s \ 
   CMD curl --fail localhost:5000/health || exit 1

COPY init-clip.py /

RUN python3 /init-clip.py

COPY startup-dev.sh /
RUN chmod +x startup-dev.sh

COPY *.py /

WORKDIR /

ENV FLASK_APP=flaskapp

# add path to gunicorn
ENV PATH="${PATH}:/root/.local/bin/"

COPY flaskapp/ /flaskapp
