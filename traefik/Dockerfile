FROM traefik:v3.8

COPY *.crt /
COPY *.key /

RUN mkdir -p /configuration/

COPY traefik.yaml /configuration/
