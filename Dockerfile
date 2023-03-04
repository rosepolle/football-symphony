FROM python:3.9-slim
RUN apt-get update && apt-get upgrade -y
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt ./requirements.txt
#RUN apt install libasound2 && apt install libasound2-dev
RUN pip install -r requirements.txt
COPY . ./
CMD gunicorn -b 0.0.0.0:80 app.app:server

