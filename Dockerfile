FROM            python:3.6.15-buster

WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt
