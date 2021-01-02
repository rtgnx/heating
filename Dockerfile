FROM python:3.9-alpine

RUN apk update && apk add alpine-sdk && libffi-dev openssl-dev

ADD ./heating.py /
ADD ./config.json /
RUN pip install meross-iot click
CMD ["/usr/bin/env", "python", "/heating.py"]
