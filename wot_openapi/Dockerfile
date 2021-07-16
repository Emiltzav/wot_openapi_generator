FROM python:3.7-alpine
MAINTAINER Aimilios Tzavaras "atzavaras@isc.tuc.gr"

WORKDIR /code
ENV FLASK_APP=generator.py   
ENV FLASK_RUN_HOST 0.0.0.0

RUN apk add --no-cache python3-dev && pip3 install --upgrade pip 
RUN apk add --no-cache gcc musl-dev linux-headers

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5001
CMD ["flask", "run"]
