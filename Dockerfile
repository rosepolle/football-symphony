FROM python:3.9-slim
RUN apt-get update && apt-get upgrade -y
RUN apt-get update && apt-get install -y gcc
RUN apt-get update && apt-get install -y libasound2-dev
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . ./
#RUN cd assets
#RUN #ls assets
CMD gunicorn -b 0.0.0.0:80 app.app:server

