FROM python:3.8-slim

WORKDIR /usr/src/app

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install -y --no-install-recommends git
RUN git config --global --add safe.directory /usr/src/app

EXPOSE 7860

ENV GRADIO_SERVER_NAME="0.0.0.0"

ENTRYPOINT ["gradio", "main_docker.py"]