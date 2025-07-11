FROM ubuntu:24.04

# https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/reference.md#run---mounttypecache
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt install -y --no-install-recommends nano ca-certificates python3 python3-pip python3-venv python3-flask curl detox imagemagick ffmpeg fdupes && \
    apt -y upgrade && \
    apt autoremove -y

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# https://docs.docker.com/build/guide/mounts/#add-a-cache-mount
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked pip3 install chromadb open-clip-torch gunicorn flask-compress humanize transformers einops rq

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s \
   CMD curl --fail localhost:5000/health || exit 1

COPY init-clip.py /
COPY init-blip.py /

RUN HF_HOME=/root/.cache/huggingface && python3 /init-clip.py && python3 /init-blip.py

# these settings are extremely conservative, we need to bump up memory and processing
# so we can handle larger image sizes during conversion
RUN rm -f /etc/ImageMagick-6/policy.xml

COPY startup-dev.sh /
RUN chmod +x startup-dev.sh

COPY *.py /

WORKDIR /

ENV FLASK_APP=flaskapp

# add path to gunicorn
ENV PATH="${PATH}:/root/.local/bin/"

COPY flaskapp/ /flaskapp
