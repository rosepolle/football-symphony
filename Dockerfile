FROM python:3.9-slim
COPY requirements.txt ./requirements.txt
RUN apt-get update && apt install libasound2 && apt install libasound2-dev
RUN pip install -r requirements.txt
COPY . ./
CMD gunicorn -b 0.0.0.0:80 app.app:server

