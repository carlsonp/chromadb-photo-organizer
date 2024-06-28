FROM traefik:v3.1

COPY *.crt /
COPY *.key /

RUN mkdir -p /configuration/

COPY traefik.yaml /configuration/
