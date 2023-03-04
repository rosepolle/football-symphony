FROM python:3.9-slim
RUN apt-get update && apt-get upgrade -y
RUN yum update -y
RUN yum groupinstall 'Development Tools' -y
COPY requirements.txt ./requirements.txt
#RUN apt install libasound2 && apt install libasound2-dev
RUN pip install -r requirements.txt
COPY . ./
CMD gunicorn -b 0.0.0.0:80 app.app:server

