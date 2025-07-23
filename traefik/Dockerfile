FROM traefik:v3.5

COPY *.crt /
COPY *.key /

RUN mkdir -p /configuration/

COPY traefik.yaml /configuration/
