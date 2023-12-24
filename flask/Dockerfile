FROM ubuntu:22.04

# for the local apt-cacher-ng proxy
RUN echo 'Acquire::HTTP::Proxy "http://192.168.1.226:3142";' >> /etc/apt/apt.conf.d/01proxy && \
    echo 'Acquire::HTTPS::Proxy "false";' >> /etc/apt/apt.conf.d/01proxy

RUN apt update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt install -y --no-install-recommends nano ca-certificates python3 python3-pip python3-flask && \
    apt -y upgrade && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

#RUN pip3 install --user flask