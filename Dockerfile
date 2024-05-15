FROM python:3.9

RUN apt-get update
RUN apt-get install -yq ffmpeg
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
WORKDIR /app
COPY . /app
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"
CMD ["python", "/app/main.py"]
