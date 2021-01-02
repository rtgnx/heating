FROM python:3.9-alpine


ADD ./heating.py /
ADD ./config.json /
RUN pip install meross-iot click
CMD ["/usr/bin/env", "python", "/heating.py"]
