FROM traefik:v3.7

COPY *.crt /
COPY *.key /

RUN mkdir -p /configuration/

COPY traefik.yaml /configuration/
