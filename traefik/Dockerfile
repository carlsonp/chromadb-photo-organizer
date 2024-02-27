FROM traefik:v2.10

COPY *.crt /
COPY *.key /

RUN mkdir -p /configuration/

COPY traefik.yaml /configuration/