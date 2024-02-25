FROM ubuntu:22.04

# for the local apt-cacher-ng proxy
# RUN echo 'Acquire::HTTP::Proxy "http://192.168.1.226:3142";' >> /etc/apt/apt.conf.d/01proxy && \
#     echo 'Acquire::HTTPS::Proxy "false";' >> /etc/apt/apt.conf.d/01proxy

RUN apt update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt install -y --no-install-recommends nano ca-certificates python3 python3-pip python3-flask curl && \
    apt -y upgrade && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --user --no-cache chromadb open-clip-torch gunicorn

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s \ 
   CMD curl --fail localhost:5000/health || exit 1

COPY init-clip.py /

RUN python3 /init-clip.py

COPY *.py /

WORKDIR /

ENV FLASK_APP=flaskapp

COPY flaskapp/ /flaskapp

# for debugging/development
CMD ["flask", "run", "--with-threads", "--debugger", "--host=0.0.0.0"]
# for production
#CMD [ "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "'flaskapp:create_app()'"]